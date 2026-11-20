// TruThorCore.h - TruMenu 0.22.68 (package B2 point 1): where the pushable Thor pillar can stand and where it can be
// pushed to, from the terrain collision faces of its unit (ENGINE 9 "Thor pillar reach from the terrain mesh (A3)").
// Pure computation, no game access: TruMenu copies the faces on the game thread and runs Build() on a background
// thread; selftest/TruThorCoreTest.cpp runs the same code on faces read from the unit file (cross-check of the two
// proven pillar spots). Port of work/a3_2011/reach_map.py:
//   raster   every face sampled at <= cell * 0.4 (10 u at 25-u cells): P0 + (i/n) u + (j/n) w, i + j <= n, n = ceil(longest
//            edge / (cell * 0.4)); per cell the highest sample in [floor - below, floor + above] ("top"), none = hole
//   blocked  top - floor > step, or hole, or a cell centre inside an obstacle disc (measured extent)
//   valid    the flat distance from the cell centre to the nearest blocked cell centre (outside the grid = blocked) is
//            larger than the foot radius (exact Euclidean distance transform, Felzenszwalb / Huttenlocher)
//   reach    8-neighbour flood fill over valid cells from the pillar's cell
//   targets  ledges (markup lines): rings (closed loops) and galleries (open ledges chained by end points < 300 flat /
//            < 100 high); a gallery within 1500 (flat, height < 150) of an artifact is that artifact's; of the rest the one
//            nearest a trigger is the exit; left-over galleries join the nearest assigned gallery at the same height
//            (< 100) within 3000; a ring leads to the nearest edge above it (flat gap <= 900, rise 0 .. 500): an artifact
//            gallery -> that artifact, any other edge -> the exit, none -> no next target
//   areas    reachable cells with (flat distance to a ring) - head <= gap, per ring; galleries direct only on request
#pragma once
#include <vector>
#include <cmath>
#include <cstring>
#include <cstdio>

namespace thorcore {

const int kExit = 0, kArtA = 1, kArtB = 2, kKinds = 3, kNoKind = -1;
const int kMaxLedgePts = 64, kMaxRings = 8;

struct Face { float v[9]; };                 // world x y z of the three corners
struct Obstacle { float x, y, r; };          // flat disc that blocks cells (centre inside = blocked)

struct Params {
    float floorZ = 0.0f;                     // the chamber floor (the pillar's floor query)
    float step = 10.0f;                      // [Puzzle] ThorStep
    float foot = 290.0f;                     // [Puzzle] ThorFoot
    float cell = 25.0f;
    float below = 60.0f, above = 1450.0f;    // the height band of the raster around the floor
    float head = 552.0f;                     // the pillar's top grab ring (object markup)
    float gap = 600.0f;                      // [Puzzle] ThorGap
    bool galleryDirect = false;              // [Puzzle] ThorGalleryDirect
};

struct Ledge {
    int id;                                  // caller's number (markup box index / markup id)
    bool closed;                             // ring
    bool target;                             // within the target band (rings / galleries 1700 .. 2200 above the floor)
    int n;
    float pts[kMaxLedgePts][3];
    int gal;                                 // gallery number (open ledges chained)
    int kind;                                // galleries: kExit / kArtA / kArtB / kNoKind; rings: the next target's kind
    int next;                                // rings: index of the next edge (-1 none)
    float nextGap, nextRise;                 // rings: flat gap / rise to that edge
    float zmean;
};

inline float SegDist2(const float *p, const float *a, const float *b) {   // flat distance^2 of p to segment ab
    const float dx = b[0] - a[0], dy = b[1] - a[1], l2 = dx * dx + dy * dy;
    float t = l2 > 1e-3f ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2 : 0.0f;
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    const float qx = a[0] + t * dx - p[0], qy = a[1] + t * dy - p[1];
    return qx * qx + qy * qy;
}
inline float LedgeDist(const Ledge &l, const float *p) {   // flat distance of p to the ledge line
    float best = 1e30f;
    if (l.n == 1) return sqrtf((p[0] - l.pts[0][0]) * (p[0] - l.pts[0][0]) + (p[1] - l.pts[0][1]) * (p[1] - l.pts[0][1]));
    for (int i = 0; i + 1 < l.n; ++i) {
        const float d = SegDist2(p, l.pts[i], l.pts[i + 1]);
        if (d < best) best = d;
    }
    if (l.closed && l.n > 2) {
        const float d = SegDist2(p, l.pts[l.n - 1], l.pts[0]);
        if (d < best) best = d;
    }
    return sqrtf(best);
}
inline float LedgeLedgeDist(const Ledge &a, const Ledge &b) {   // flat distance of two polylines (no crossing assumed)
    float best = 1e30f;
    for (int i = 0; i < a.n; ++i) { const float d = LedgeDist(b, a.pts[i]); if (d < best) best = d; }
    for (int i = 0; i < b.n; ++i) { const float d = LedgeDist(a, b.pts[i]); if (d < best) best = d; }
    return best;
}

// chain open target ledges into galleries, assign artifact / exit kinds, then the next target of each ring.
// art[k] = artifact k's position (k < arts, A = the lower intro id); trig = trigger positions (x y z, count trigN)
inline void Classify(std::vector<Ledge> &L, const float art[2][3], int arts, const float *trig, int trigN, char *log,
                     size_t logN) {
    const int n = static_cast<int>(L.size());
    for (int k = 0; k < n; ++k) {
        float z = 0.0f;
        for (int i = 0; i < L[k].n; ++i) z += L[k].pts[i][2];
        L[k].zmean = L[k].n ? z / static_cast<float>(L[k].n) : 0.0f;
        L[k].gal = k;
        L[k].kind = kNoKind;
        L[k].next = -1;
        L[k].nextGap = L[k].nextRise = 0.0f;
    }
    auto isGal = [&](int k) { return !L[k].closed && L[k].target; };
    for (bool merged = true; merged;) {
        merged = false;
        for (int a = 0; a < n; ++a)
            for (int b = a + 1; b < n; ++b) {
                if (!isGal(a) || !isGal(b) || L[a].gal == L[b].gal) continue;
                bool joined = false;
                for (int ea = 0; ea < 2 && !joined; ++ea)
                    for (int eb = 0; eb < 2 && !joined; ++eb) {
                        const float *pa = L[a].pts[ea ? L[a].n - 1 : 0], *pb = L[b].pts[eb ? L[b].n - 1 : 0];
                        const float dx = pa[0] - pb[0], dy = pa[1] - pb[1];
                        joined = dx * dx + dy * dy < 300.0f * 300.0f && fabsf(pa[2] - pb[2]) < 100.0f;
                    }
                if (!joined) continue;
                const int from = L[b].gal, to = L[a].gal;
                for (int k = 0; k < n; ++k)
                    if (L[k].gal == from) L[k].gal = to;
                merged = true;
            }
    }
    std::vector<int> galKind(static_cast<size_t>(n), -2);   // -2 no gallery, -1 open without kind
    for (int k = 0; k < n; ++k)
        if (isGal(k)) galKind[static_cast<size_t>(L[k].gal)] = -1;
    for (int k = 0; k < n; ++k) {             // artifact galleries: within 1500 flat and < 150 in height
        if (!isGal(k)) continue;
        for (int q = 0; q < arts; ++q)
            if (LedgeDist(L[k], art[q]) < 1500.0f && fabsf(L[k].zmean - art[q][2]) < 150.0f &&
                galKind[static_cast<size_t>(L[k].gal)] == -1)
                galKind[static_cast<size_t>(L[k].gal)] = q == 0 ? kArtA : kArtB;
    }
    int exitGal = -1;                         // exit: the open gallery nearest a trigger
    float exitD = 1e30f;
    for (int t = 0; t < trigN; ++t)
        for (int k = 0; k < n; ++k) {
            if (!isGal(k) || galKind[static_cast<size_t>(L[k].gal)] != -1) continue;
            const float d = LedgeDist(L[k], trig + 3 * t);
            if (d < exitD) { exitD = d; exitGal = L[k].gal; }
        }
    if (exitGal >= 0) galKind[static_cast<size_t>(exitGal)] = kExit;
    // left-over galleries: the kind of the nearest assigned gallery at the same height (< 100) within 3000
    for (int k = 0; k < n; ++k) {
        if (!isGal(k) || galKind[static_cast<size_t>(L[k].gal)] != -1) continue;
        float best = 3000.0f;
        int kind = -1;
        for (int j = 0; j < n; ++j) {
            if (!isGal(j) || galKind[static_cast<size_t>(L[j].gal)] < 0 || fabsf(L[j].zmean - L[k].zmean) >= 100.0f) continue;
            const float d = LedgeLedgeDist(L[k], L[j]);
            if (d < best) { best = d; kind = galKind[static_cast<size_t>(L[j].gal)]; }
        }
        if (kind >= 0) {
            const int g = L[k].gal;
            for (int j = 0; j < n; ++j)
                if (isGal(j) && L[j].gal == g) galKind[static_cast<size_t>(g)] = kind;
            if (log && logN) {
                const size_t u = strlen(log);
                _snprintf_s(log + u, logN - u, _TRUNCATE, "%sgallery %d joins the nearest gallery (%.0f u, kind %d)",
                            u ? "; " : "", L[k].id, static_cast<double>(best), kind);
            }
        }
    }
    for (int k = 0; k < n; ++k)
        if (isGal(k)) L[k].kind = galKind[static_cast<size_t>(L[k].gal)] >= 0 ? galKind[static_cast<size_t>(L[k].gal)] : kNoKind;
    // rings: the nearest edge above (flat gap <= 900, rise 0 .. 500), open ledges only
    for (int r = 0; r < n; ++r) {
        if (!L[r].closed || !L[r].target) continue;
        float best = 900.0f;
        for (int k = 0; k < n; ++k) {
            if (k == r || L[k].closed) continue;
            const float rise = L[k].zmean - L[r].zmean;
            if (rise < 0.0f || rise > 500.0f) continue;
            const float d = LedgeLedgeDist(L[r], L[k]);
            if (d <= best) { best = d; L[r].next = k; L[r].nextGap = d; L[r].nextRise = rise; }
        }
        L[r].kind = L[r].next < 0 ? kNoKind : (L[L[r].next].kind == kArtA || L[L[r].next].kind == kArtB) ? L[L[r].next].kind
                                                                                                          : kExit;
    }
}

struct Result {
    Params P;
    float x0 = 0.0f, y0 = 0.0f;
    int nx = 0, ny = 0;
    int facesUsed = 0;
    std::vector<float> top;                  // highest sample z per cell (-1e30 = hole)
    std::vector<unsigned char> blocked, valid, reach;
    std::vector<float> dist;                 // units to the nearest blocked cell centre
    std::vector<unsigned char> ringMask;     // bit r = in the area of ring r (index into rings)
    std::vector<unsigned char> galMask;      // bit kind = in the direct area of a gallery of that kind
    std::vector<int> rings;                  // ledge index per ring bit
    int startCell = -1, startFrom = -1;      // flood start (after the <= 50-u search) and the pillar's own cell
    int validN = 0, reachN = 0;
    int hist[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};   // rise 0..2 / 2..6 / 6..10 / 10..20 / 20..40 / 40..100 / 100..300 / >300 / hole
    int Index(float x, float y) const {
        if (!(x >= x0 && y >= y0)) return -1;
        const int ix = static_cast<int>((x - x0) / P.cell), iy = static_cast<int>((y - y0) / P.cell);
        return ix < nx && iy < ny ? iy * nx + ix : -1;
    }
    float Cx(int i) const { return x0 + (static_cast<float>(i % nx) + 0.5f) * P.cell; }
    float Cy(int i) const { return y0 + (static_cast<float>(i / nx) + 0.5f) * P.cell; }
    float Rise(int i) const { return top[static_cast<size_t>(i)] < -1e29f ? 1e30f : top[static_cast<size_t>(i)] - P.floorZ; }
    // the nearest blocked cell to (x, y) within lim units: its index, -1 none
    int NearestBlocked(float x, float y, float lim, float *d) const {
        const int c = Index(x, y);
        *d = 1e30f;
        if (c < 0) return -1;
        const int r = static_cast<int>(lim / P.cell) + 1, cx = c % nx, cy = c / nx;
        int best = -1;
        for (int j = cy - r; j <= cy + r; ++j)
            for (int i = cx - r; i <= cx + r; ++i) {
                if (i < 0 || j < 0 || i >= nx || j >= ny || !blocked[static_cast<size_t>(j * nx + i)]) continue;
                const float dx = Cx(j * nx + i) - x, dy = Cy(j * nx + i) - y, dd = sqrtf(dx * dx + dy * dy);
                if (dd < *d) { *d = dd; best = j * nx + i; }
            }
        return best;
    }
};

// 1-D squared distance transform (Felzenszwalb / Huttenlocher) of f (n values) into d; v / z scratch
inline void Edt1(const float *f, int n, float *d, int *v, float *z) {
    int k = 0;
    v[0] = 0;
    z[0] = -1e30f;
    z[1] = 1e30f;
    for (int q = 1; q < n; ++q) {
        float s = ((f[q] + static_cast<float>(q) * q) - (f[v[k]] + static_cast<float>(v[k]) * v[k])) /
                  (2.0f * static_cast<float>(q - v[k]));
        while (s <= z[k]) {
            --k;
            s = ((f[q] + static_cast<float>(q) * q) - (f[v[k]] + static_cast<float>(v[k]) * v[k])) /
                (2.0f * static_cast<float>(q - v[k]));
        }
        ++k;
        v[k] = q;
        z[k] = s;
        z[k + 1] = 1e30f;
    }
    k = 0;
    for (int q = 0; q < n; ++q) {
        while (z[k + 1] < static_cast<float>(q)) ++k;
        const float dq = static_cast<float>(q - v[k]);
        d[q] = dq * dq + f[v[k]];
    }
}

// raster + blocked + distance + valid + flood from (sx, sy) + areas. Box x0 .. x1, y0 .. y1 (cells of P.cell).
// faceN < 0: no faces - R.top is already filled (nx * ny cells, the ray fallback of TruMenu)
inline bool Build(Result &R, const Params &P, const Face *faces, int faceN, const Obstacle *obs, int obsN,
                  const std::vector<Ledge> &L, float bx0, float bx1, float by0, float by1, float sx, float sy) {
    R.P = P;
    R.x0 = bx0;
    R.y0 = by0;
    R.nx = static_cast<int>(ceilf((bx1 - bx0) / P.cell));
    R.ny = static_cast<int>(ceilf((by1 - by0) / P.cell));
    if (R.nx < 4 || R.ny < 4 || R.nx > 1200 || R.ny > 1200) return false;
    const size_t N = static_cast<size_t>(R.nx) * static_cast<size_t>(R.ny);
    if (faceN < 0 && R.top.size() != N) return false;
    if (faceN >= 0) R.top.assign(N, -1e30f);
    const double zlo = static_cast<double>(P.floorZ) - P.below, zhi = static_cast<double>(P.floorZ) + P.above;
    const double cell = P.cell, x0 = bx0, y0 = by0, x1 = bx1, y1 = by1;
    R.facesUsed = 0;
    for (int f = 0; f < faceN; ++f) {
        const float *v = faces[f].v;
        double mnx = v[0], mxx = v[0], mny = v[1], mxy = v[1], mnz = v[2], mxz = v[2];
        for (int c = 1; c < 3; ++c) {
            mnx = v[3 * c] < mnx ? v[3 * c] : mnx; mxx = v[3 * c] > mxx ? v[3 * c] : mxx;
            mny = v[3 * c + 1] < mny ? v[3 * c + 1] : mny; mxy = v[3 * c + 1] > mxy ? v[3 * c + 1] : mxy;
            mnz = v[3 * c + 2] < mnz ? v[3 * c + 2] : mnz; mxz = v[3 * c + 2] > mxz ? v[3 * c + 2] : mxz;
        }
        if (mxx < x0 || mnx > x1 || mxy < y0 || mny > y1 || mxz < zlo || mnz > zhi) continue;
        ++R.facesUsed;
        const double ux = static_cast<double>(v[3]) - v[0], uy = static_cast<double>(v[4]) - v[1], uz = static_cast<double>(v[5]) - v[2];
        const double wx = static_cast<double>(v[6]) - v[0], wy = static_cast<double>(v[7]) - v[1], wz = static_cast<double>(v[8]) - v[2];
        const double ex = static_cast<double>(v[6]) - v[3], ey = static_cast<double>(v[7]) - v[4], ez = static_cast<double>(v[8]) - v[5];
        double len = sqrt(ux * ux + uy * uy + uz * uz);
        const double lw = sqrt(wx * wx + wy * wy + wz * wz), le = sqrt(ex * ex + ey * ey + ez * ez);
        len = lw > len ? lw : len;
        len = le > len ? le : len;
        int n = static_cast<int>(ceil(len / (cell * 0.4)));
        if (n < 1) n = 1;
        if (n > 4000) n = 4000;
        for (int i = 0; i <= n; ++i)
            for (int j = 0; j <= n - i; ++j) {
                const double a = static_cast<double>(i) / n, b = static_cast<double>(j) / n;
                const double px = v[0] + a * ux + b * wx, py = v[1] + a * uy + b * wy, pz = v[2] + a * uz + b * wz;
                if (pz < zlo || pz > zhi || px < x0 || px >= x1 || py < y0 || py >= y1) continue;
                const int ix = static_cast<int>(floor((px - x0) / cell)), iy = static_cast<int>(floor((py - y0) / cell));
                if (ix < 0 || iy < 0 || ix >= R.nx || iy >= R.ny) continue;
                float &t = R.top[static_cast<size_t>(iy) * static_cast<size_t>(R.nx) + static_cast<size_t>(ix)];
                if (static_cast<float>(pz) > t) t = static_cast<float>(pz);
            }
    }
    R.blocked.assign(N, 0);
    memset(R.hist, 0, sizeof(R.hist));
    const float bands[8] = {2.0f, 6.0f, 10.0f, 20.0f, 40.0f, 100.0f, 300.0f, 1e30f};
    for (size_t i = 0; i < N; ++i) {
        const bool hole = R.top[i] < -1e29f;
        const float rise = hole ? 1e30f : R.top[i] - P.floorZ;
        if (hole) ++R.hist[8];
        else for (int b = 0; b < 8; ++b) if (rise <= bands[b]) { ++R.hist[b]; break; }
        R.blocked[i] = static_cast<unsigned char>(!(rise <= P.step) ? 1 : 0);
    }
    for (int q = 0; q < obsN; ++q) {          // obstacle discs
        const int r = static_cast<int>(obs[q].r / P.cell) + 1;
        const int c = R.Index(obs[q].x, obs[q].y);
        if (c < 0) continue;
        for (int j = c / R.nx - r; j <= c / R.nx + r; ++j)
            for (int i = c % R.nx - r; i <= c % R.nx + r; ++i) {
                if (i < 0 || j < 0 || i >= R.nx || j >= R.ny) continue;
                const float dx = R.Cx(j * R.nx + i) - obs[q].x, dy = R.Cy(j * R.nx + i) - obs[q].y;
                if (dx * dx + dy * dy <= obs[q].r * obs[q].r) R.blocked[static_cast<size_t>(j * R.nx + i)] = 1;
            }
    }
    // exact distance transform on the grid padded by one blocked cell all round (outside = blocked)
    const int px = R.nx + 2, py = R.ny + 2, m = px > py ? px : py;
    std::vector<float> g(static_cast<size_t>(px) * static_cast<size_t>(py)), f(static_cast<size_t>(m)),
        d(static_cast<size_t>(m)), z(static_cast<size_t>(m) + 1);
    std::vector<int> vv(static_cast<size_t>(m));
    const float big = 4.0f * static_cast<float>(m) * static_cast<float>(m);   // > any squared distance, still exact in float
    for (int j = 0; j < py; ++j)
        for (int i = 0; i < px; ++i) {
            const bool b = i == 0 || j == 0 || i == px - 1 || j == py - 1 ||
                           R.blocked[static_cast<size_t>(j - 1) * static_cast<size_t>(R.nx) + static_cast<size_t>(i - 1)];
            g[static_cast<size_t>(j) * static_cast<size_t>(px) + static_cast<size_t>(i)] = b ? 0.0f : big;
        }
    for (int i = 0; i < px; ++i) {            // columns
        for (int j = 0; j < py; ++j) f[static_cast<size_t>(j)] = g[static_cast<size_t>(j) * static_cast<size_t>(px) + static_cast<size_t>(i)];
        Edt1(f.data(), py, d.data(), vv.data(), z.data());
        for (int j = 0; j < py; ++j) g[static_cast<size_t>(j) * static_cast<size_t>(px) + static_cast<size_t>(i)] = d[static_cast<size_t>(j)];
    }
    for (int j = 0; j < py; ++j) {            // rows
        Edt1(&g[static_cast<size_t>(j) * static_cast<size_t>(px)], px, d.data(), vv.data(), z.data());
        memcpy(&g[static_cast<size_t>(j) * static_cast<size_t>(px)], d.data(), sizeof(float) * static_cast<size_t>(px));
    }
    R.dist.assign(N, 0.0f);
    R.valid.assign(N, 0);
    R.validN = 0;
    for (int j = 0; j < R.ny; ++j)
        for (int i = 0; i < R.nx; ++i) {
            const size_t k = static_cast<size_t>(j) * static_cast<size_t>(R.nx) + static_cast<size_t>(i);
            R.dist[k] = sqrtf(g[static_cast<size_t>(j + 1) * static_cast<size_t>(px) + static_cast<size_t>(i + 1)]) * P.cell;
            R.valid[k] = static_cast<unsigned char>(R.dist[k] > P.foot ? 1 : 0);
            R.validN += R.valid[k];
        }
    // flood fill from the pillar's cell (or the nearest valid cell within 50 units)
    R.reach.assign(N, 0);
    R.reachN = 0;
    R.startFrom = R.Index(sx, sy);
    R.startCell = -1;
    if (R.startFrom >= 0) {
        if (R.valid[static_cast<size_t>(R.startFrom)]) R.startCell = R.startFrom;
        else {
            float bd = 50.0f;
            const int rr = static_cast<int>(50.0f / P.cell) + 1, cx = R.startFrom % R.nx, cy = R.startFrom / R.nx;
            for (int j = cy - rr; j <= cy + rr; ++j)
                for (int i = cx - rr; i <= cx + rr; ++i) {
                    if (i < 0 || j < 0 || i >= R.nx || j >= R.ny || !R.valid[static_cast<size_t>(j * R.nx + i)]) continue;
                    const float dx = R.Cx(j * R.nx + i) - sx, dy = R.Cy(j * R.nx + i) - sy, dd = sqrtf(dx * dx + dy * dy);
                    if (dd <= bd) { bd = dd; R.startCell = j * R.nx + i; }
                }
        }
    }
    if (R.startCell >= 0) {
        std::vector<int> q;
        q.reserve(4096);
        q.push_back(R.startCell);
        R.reach[static_cast<size_t>(R.startCell)] = 1;
        for (size_t h = 0; h < q.size(); ++h) {
            const int a = q[h] % R.nx, b = q[h] / R.nx;
            for (int db = -1; db <= 1; ++db)
                for (int da = -1; da <= 1; ++da) {
                    const int c = a + da, e = b + db;
                    if (c < 0 || e < 0 || c >= R.nx || e >= R.ny) continue;
                    const size_t k = static_cast<size_t>(e) * static_cast<size_t>(R.nx) + static_cast<size_t>(c);
                    if (!R.valid[k] || R.reach[k]) continue;
                    R.reach[k] = 1;
                    q.push_back(static_cast<int>(k));
                }
        }
        R.reachN = static_cast<int>(q.size());
    }
    // areas: reachable cells near a ring (per ring) / a gallery of a kind (direct, on request)
    R.rings.clear();
    for (size_t k = 0; k < L.size() && R.rings.size() < static_cast<size_t>(kMaxRings); ++k)
        if (L[k].closed && L[k].target) R.rings.push_back(static_cast<int>(k));
    R.ringMask.assign(N, 0);
    R.galMask.assign(N, 0);
    for (size_t i = 0; i < N; ++i) {
        if (!R.reach[i]) continue;
        const float c[3] = {R.Cx(static_cast<int>(i)), R.Cy(static_cast<int>(i)), P.floorZ};
        for (size_t r = 0; r < R.rings.size(); ++r)
            if (LedgeDist(L[static_cast<size_t>(R.rings[r])], c) - P.head <= P.gap) R.ringMask[i] |= static_cast<unsigned char>(1u << r);
        if (!P.galleryDirect) continue;
        for (size_t k = 0; k < L.size(); ++k)
            if (!L[k].closed && L[k].target && L[k].kind >= 0 && LedgeDist(L[k], c) - P.head <= P.gap)
                R.galMask[i] |= static_cast<unsigned char>(1u << L[k].kind);
    }
    return true;
}

}  // namespace thorcore
