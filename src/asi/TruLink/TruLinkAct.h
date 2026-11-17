// TruLinkAct.h - TruLink 0.5 game-calling actions, shared by TruLink.asi (obj.place / uber.send cmd / joint.drive)
// and TruMenu.asi 0.22.56 (page Kapitel "Raetsel in der Naehe": bring a weight, set the shadow figures, hold a door
// open). Moved unchanged out of TruLink.cpp 0.5 (TruLink 0.5.1), so both plugins run the same code:
//   - PlaceBody: the game's own placement path for a physics object (INSTANCE_SetPosition 0x5b4100, optional
//     INSTANCE_SetRotation 0x5b4040, body <- instance 0x497740, velocity 0, wake) - ENGINE section 5.2;
//   - CmdExec: entry n of an object command table through the multibody's own vf+4 = 0x4d77a0 (ENGINE section 9);
//   - DriveCtl / DriveTick / DriveStop: joint.drive with the joint's own motor (velocity per physics tick, limits
//     untouched) including 0.5 hold-until-off.
// The includer provides (besides TruLinkObj.h's TlRead / TlAdd / TlJointValue):
//   void TlLog(int level, const char *fmt, ...);   its log
//   void TlReadReset();                            forget TlRead's region cache (one call per tick)
// Every address used here is a byte check row of TruLinkObj.h (groups place, command, joint, drive); callers check
// those groups before they call anything here, on the game thread.
#pragma once
#include "TruLinkObj.h"

void TlLog(int level, _Printf_format_string_ const char *fmt, ...);
void TlReadReset();

namespace tlact {

typedef void(__cdecl *InstVecFn)(void *inst, const float *v);
typedef void(__cdecl *BodyToInstFn)(void *body, void *inst);
typedef void(__thiscall *BodyVecFn)(void *body, const float *v);
typedef void(__thiscall *BodyFn)(void *body);
typedef void(__thiscall *CmdExecFn)(void *x, int n);
typedef void(__thiscall *JtSetAxisFn)(void *joint, int axis, float value);
typedef void(__thiscall *JtEnableFn)(void *joint, int axis, int on);
typedef void(__thiscall *JtWakeFn)(void *body);

// ---- obj.place (TruLink 0.5) ----
inline bool PlaceCalls(DWORD inst, DWORD body, const float *p, const float *r, const float *zero) {
    __try {
        reinterpret_cast<InstVecFn>(tlobj::kSetPos)(reinterpret_cast<void *>(inst), p);
        if (r) reinterpret_cast<InstVecFn>(tlobj::kSetRot)(reinterpret_cast<void *>(inst), r);
        reinterpret_cast<BodyToInstFn>(tlobj::kBodyToInst)(reinterpret_cast<void *>(body), reinterpret_cast<void *>(inst));
        reinterpret_cast<BodyVecFn>(tlobj::kBodyLinVel)(reinterpret_cast<void *>(body), zero);
        reinterpret_cast<BodyVecFn>(tlobj::kBodyAngVel)(reinterpret_cast<void *>(body), zero);
        reinterpret_cast<BodyFn>(tlobj::kJtWake)(reinterpret_cast<void *>(body));
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
    return true;
}
// pos: new instance origin; rot: new instance rotation (rad) or nullptr = keep
inline bool PlaceBody(DWORD inst, const float *pos, const float *rot) {
    const DWORD body = tlobj::BodyOf(inst);
    if (!body) return false;
    float w = 0.0f;
    tlobj::RF(inst + 0x2c, &w);                                // keep the 4th word: 0x5c55b0 moves by (new - old) as vec4
    __declspec(align(16)) float p[4] = {pos[0], pos[1], pos[2], w};
    __declspec(align(16)) float r[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    __declspec(align(16)) float zero[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    if (rot) {
        r[0] = rot[0]; r[1] = rot[1]; r[2] = rot[2];
        tlobj::RF(inst + 0x3c, &r[3]);
    }
    return PlaceCalls(inst, body, p, rot ? r : nullptr, zero);
}

// ---- uber.send cmd (TruLink 0.4): X vf+4 = 0x4d77a0, the call uber action 11 / a script command makes ----
// false = X's vf+4 is not 0x4d77a0 (refused) or an access fault (caught)
inline bool CmdExec(DWORD x, int n) {
    if (tlobj::D(tlobj::D(x) + 4) != tlobj::kCmdExec) return false;
    __try {
        reinterpret_cast<CmdExecFn>(tlobj::kCmdExec)(reinterpret_cast<void *>(x), n);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
    return true;
}

// ---- joint.drive: the joint's own motor (velocity + force, axis 0) towards a target; the limits stay as they are ----
// 2026-11-15: TruMenu 0.22.53 joint.set (lock lo = hi = target) drove the l3_chapel shadow door rail from -0.84 to -1115
// - the lock replaced the joint's limits [0, 948.2], nothing held the body. joint.drive never touches the limits: the
// target is clamped inside them (limit on, lo < hi), the motor pushes at a ramped velocity with a bounded force, and the
// drive stops (saved motor velocity / force / enable put back) on: reached (after the hold), moving away from the target
// (one sign flip allowed - the motor sign is not proven), overshoot, a step larger than 4x the commanded one, leaving
// the limits, no progress for 1.5 s, a node change of any linked uber, 10 s, or joint.drive stop.
struct Drive {
    DWORD inst, stamp, x, joint, jrec;
    LONG intro;
    int index, type, sign, flips, lines, journal;
    float target, from, best, lastV, speed, force, lo, hi, vel, hold;
    bool limits, through;                    // through: go on over node changes of the linked ubers (logged)
    bool holdOff;                            // 0.5 hold-until-off: no time limit, keeps the target until stop / hold off
    DWORD lastHoldLog;
    int corrections;                         // 0.5: hold mode - times the joint was pushed off and driven back
    float saveVel, saveForce;
    bool saveMotor;
    DWORD start, lastTick, lastBetter, reached, clock;
    DWORD nodes[64];                         // node + transition of each linked uber at the start
    int links;
};
// one running drive of a plugin: TruLink's joint.drive, TruMenu's puzzle.hold (each its own)
struct DriveCtl {
    Drive d;
    volatile LONG on;
    const char *tag;                         // log prefix: "joint.drive" (TruLink), "puzzle.hold" (TruMenu)
    void (*ended)(int journal);              // called by DriveStop (TruLink: the journal row has nothing left to undo)
};

// vel / force in the engine's units: velocity per physics tick (hinge rad/tick, rail units/tick, tlobj::kTicksPerSecond)
inline void JtMotor(DWORD joint, float vel, float force, bool on) {
    void *j = reinterpret_cast<void *>(joint);
    reinterpret_cast<JtSetAxisFn>(tlobj::kJtMotorVel)(j, 0, vel);
    reinterpret_cast<JtSetAxisFn>(tlobj::kJtMotorForce)(j, 0, force);
    const bool isOn = (tlobj::D(joint + 0x174) & 0x10) != 0;
    if (isOn != on) reinterpret_cast<JtEnableFn>(tlobj::kJtMotorOn)(j, 0, on ? 1 : 0);
}
inline void JtWakeBodies(DWORD joint) {
    const DWORD a = tlobj::D(joint + 0x160), b = tlobj::D(joint + 0x15c);
    if (a) reinterpret_cast<JtWakeFn>(tlobj::kJtWake)(reinterpret_cast<void *>(a));
    if (b) reinterpret_cast<JtWakeFn>(tlobj::kJtWake)(reinterpret_cast<void *>(b));
}
inline DWORD LinkState(DWORD x, int i) {
    const DWORD li = tlobj::LinkInst(x, i), b = li ? tlobj::Uber(li) : 0;
    return b ? (tlobj::D(b + 0x84) & 0xffff) | (tlobj::D(b + 0x80) ? 0x10000u : 0u) : 0xffffffffu;
}
// stop: put the saved motor settings back when the joint still carries ours (a node action may have set its own)
inline void DriveStop(DriveCtl &c, const char *why) {
    if (!c.on) return;
    InterlockedExchange(&c.on, 0);
    Drive &g_drv = c.d;
    float v = 0.0f, vel = 0.0f, force = 0.0f;
    const bool alive = tlobj::D(g_drv.inst + 0x44) == g_drv.stamp && tlobj::JointType(g_drv.joint) == g_drv.type;
    bool restored = false;
    if (alive && tlobj::RF(g_drv.joint + 0x108, &vel) && tlobj::RF(g_drv.joint + 0x10c, &force) && force == g_drv.force) {
        __try {
            JtMotor(g_drv.joint, g_drv.saveVel, g_drv.saveForce, g_drv.saveMotor);
            restored = true;
        } __except (EXCEPTION_EXECUTE_HANDLER) {
        }
    }
    const bool val = alive && TlJointValue(g_drv.joint, g_drv.type, &v);
    if (val && g_drv.type == 1 && g_drv.limits) v = tlobj::HingeUnwrap(v, g_drv.lo, g_drv.hi);   // 0.5.2
    if (c.ended) c.ended(g_drv.journal);     // TruLink: nothing left to undo in the journal row
    TlLog(1, "%s %ld joint %d: %s - value %s%.2f (from %.2f, target %.2f) after %.1f s; motor %s", c.tag, g_drv.intro,
          g_drv.index, why, val ? "" : "? ", static_cast<double>(v), static_cast<double>(g_drv.from),
          static_cast<double>(g_drv.target), (GetTickCount() - g_drv.start) / 1000.0,
          restored ? "settings put back (velocity / force / enable)" : alive ? "left alone (a node action changed it)" : "gone");
}
// once per game frame (clock = the game's frame clock); a fault inside is the caller's to catch
inline void DriveTick(DriveCtl &c, DWORD clock) {
    if (!c.on) return;
    Drive &g_drv = c.d;
    if (clock == g_drv.clock) return;                          // once per game frame
    g_drv.clock = clock;
    TlReadReset();
    if (tlobj::D(g_drv.inst + 0x44) != g_drv.stamp || tlobj::JointType(g_drv.joint) != g_drv.type) {
        DriveStop(c, "instance / joint gone (unit change?)");
        return;
    }
    for (int i = 0; i < g_drv.links; ++i) {
        const DWORD s = LinkState(g_drv.x, i);
        if (s != g_drv.nodes[i] && (g_drv.through || g_drv.holdOff)) {
            TlLog(1, "%s %ld joint %d: link %d node %lu -> %lu%s - going on (through 1)", c.tag, g_drv.intro, g_drv.index, i,
                  g_drv.nodes[i] & 0xffff, s & 0xffff, (s & 0x10000) ? " (transition)" : "");
            g_drv.nodes[i] = s;
        } else if (s != g_drv.nodes[i]) {
            char line[128];
            _snprintf_s(line, sizeof(line), _TRUNCATE, "stopped: link %d changed node %lu -> %lu%s (the game reacts; its node "
                        "actions own the joint now)", i, g_drv.nodes[i] & 0xffff, s & 0xffff, (s & 0x10000) ? " (transition)" : "");
            DriveStop(c, line);
            return;
        }
    }
    float v = 0.0f;
    if (!TlJointValue(g_drv.joint, g_drv.type, &v)) { DriveStop(c, "value unreadable"); return; }
    // 0.5.2: a hinge at a stop near 180 reads -180 (the getter's range) - taken back into the limits, not "outside"
    if (g_drv.type == 1 && g_drv.limits) v = tlobj::HingeUnwrap(v, g_drv.lo, g_drv.hi);
    const DWORD now = GetTickCount();
    const bool hinge = g_drv.type == 1;
    const float tol = hinge ? 0.5f : 2.0f, away = hinge ? 3.0f : 10.0f, over = hinge ? 2.0f : 5.0f, margin = hinge ? 2.0f : 5.0f;
    const float dist = fabsf(g_drv.target - v);
    const float dt = g_drv.lastTick && now > g_drv.lastTick ? (now - g_drv.lastTick) / 1000.0f : 0.0f;
    const float step = fabsf(v - g_drv.lastV);
    char line[200] = "";
    // 0.5 hold-until-off, once the target was reached: no time limit and no away / overshoot / progress stop - a push
    // off the target (Lara, the game's own motor) is driven back; only the limits, the instance and stop end it
    const bool holding = g_drv.holdOff && g_drv.reached;
    if (holding) {
        if (dist > 4.0f * tol) {
            if (dist > g_drv.best + away) {
                ++g_drv.corrections;
                TlLog(1, "%s %ld joint %d hold: pushed to %.2f (target %.2f) - driving back (#%d)", c.tag, g_drv.intro,
                      g_drv.index, static_cast<double>(v), static_cast<double>(g_drv.target), g_drv.corrections);
            }
            g_drv.best = dist;
        } else {
            g_drv.best = dist < tol ? 0.0f : dist;
        }
        if (now - g_drv.lastHoldLog > 10000) {
            g_drv.lastHoldLog = now;
            TlLog(1, "%s %ld joint %d hold: %.2f (target %.2f) for %.0f s, %d correction(s)", c.tag, g_drv.intro, g_drv.index,
                  static_cast<double>(v), static_cast<double>(g_drv.target), (now - g_drv.reached) / 1000.0, g_drv.corrections);
        }
    }
    if (g_drv.limits && (v < g_drv.lo - margin || v > g_drv.hi + margin))
        _snprintf_s(line, sizeof(line), _TRUNCATE, "stopped: value %.2f outside the joint's limits [%.2f, %.2f]",
                    static_cast<double>(v), static_cast<double>(g_drv.lo), static_cast<double>(g_drv.hi));
    else if (holding)
        ;                                                      // hold mode: the checks below are for the approach
    else if (dt > 0.0f && step > 4.0f * g_drv.speed * dt + (hinge ? 1.0f : 3.0f))
        _snprintf_s(line, sizeof(line), _TRUNCATE, "stopped: step %.2f in %.3f s is more than 4x the drive speed %.1f /s",
                    static_cast<double>(step), static_cast<double>(dt), static_cast<double>(g_drv.speed));
    else if ((g_drv.from - g_drv.target) * (v - g_drv.target) < 0.0f && dist > over)
        _snprintf_s(line, sizeof(line), _TRUNCATE, "stopped: value %.2f overshot the target %.2f", static_cast<double>(v),
                    static_cast<double>(g_drv.target));
    else if (dist > g_drv.best + away) {
        if (!g_drv.flips) {                                    // the motor sign is not proven: one flip, then stop
            g_drv.flips = 1;
            g_drv.sign = -g_drv.sign;
            g_drv.best = dist;
            g_drv.lastBetter = now;
            TlLog(1, "%s %ld joint %d: value %.2f moves away from %.2f - motor sign flipped once", c.tag, g_drv.intro,
                  g_drv.index, static_cast<double>(v), static_cast<double>(g_drv.target));
        } else {
            _snprintf_s(line, sizeof(line), _TRUNCATE, "stopped: value %.2f moves away from the target %.2f (best %.2f) after "
                        "the sign flip", static_cast<double>(v), static_cast<double>(g_drv.target), static_cast<double>(g_drv.best));
        }
    }
    if (!line[0] && !holding && dist + tol < g_drv.best) { g_drv.best = dist; g_drv.lastBetter = now; }
    if (!line[0] && dist <= tol && !g_drv.reached) {
        g_drv.reached = now ? now : 1;
        g_drv.lastHoldLog = now;
        if (g_drv.holdOff)
            TlLog(1, "%s %ld joint %d: reached %.2f after %.1f s - holding until stop / hold off", c.tag, g_drv.intro,
                  g_drv.index, static_cast<double>(v), (now - g_drv.start) / 1000.0);
    }
    if (!line[0] && !g_drv.holdOff && g_drv.reached && now - g_drv.reached > static_cast<DWORD>(g_drv.hold * 1000.0f))
        _snprintf_s(line, sizeof(line), _TRUNCATE, "reached %.2f (target %.2f), held %.1f s", static_cast<double>(v),
                    static_cast<double>(g_drv.target), static_cast<double>(g_drv.hold));
    if (!line[0] && !g_drv.reached && now - g_drv.lastBetter > 1500)
        _snprintf_s(line, sizeof(line), _TRUNCATE, "stopped: no progress for 1.5 s at %.2f (blocked: Lara, contact, a lock?)",
                    static_cast<double>(v));
    if (!line[0] && !g_drv.reached && now - g_drv.start > (g_drv.holdOff ? 30000u : 10000u))
        _snprintf_s(line, sizeof(line), _TRUNCATE, "stopped: timeout %d s at %.2f (target not reached)", g_drv.holdOff ? 30 : 10,
                    static_cast<double>(v));
    g_drv.lastV = v;
    g_drv.lastTick = now;
    if (line[0]) { DriveStop(c, line); return; }
    // the commanded velocity: proportional to the rest, at most speed, at least 10 % of it; 0 while holding (hold
    // mode: 0 inside the tolerance, else back towards the target the same way)
    const float err = g_drv.target - v;
    float cmd = 2.0f * fabsf(err);
    if (cmd > g_drv.speed) cmd = g_drv.speed;
    if (cmd < 0.1f * g_drv.speed) cmd = 0.1f * g_drv.speed;
    if (g_drv.reached && (!g_drv.holdOff || dist <= tol)) cmd = 0.0f;
    g_drv.vel = (err >= 0.0f ? 1.0f : -1.0f) * static_cast<float>(g_drv.sign) * cmd;
    // 0.5: the engine's motor velocity is per physics tick (1/30 s): deg/s -> rad/tick, units/s -> units/tick
    JtMotor(g_drv.joint, (hinge ? g_drv.vel / tlobj::kRadToDeg : g_drv.vel) / tlobj::kTicksPerSecond, g_drv.force, true);
    JtWakeBodies(g_drv.joint);
    if (g_drv.lines < 300 && !holding && (g_drv.lines < 20 || (g_drv.lines % 10) == 0))
        TlLog(1, "%s %ld joint %d t %.2f s: value %.2f target %.2f motor velocity %.2f%s force %.6g best %.2f", c.tag,
              g_drv.intro, g_drv.index, (now - g_drv.start) / 1000.0, static_cast<double>(v), static_cast<double>(g_drv.target),
              static_cast<double>(g_drv.vel), hinge ? " deg/s" : " /s", static_cast<double>(g_drv.force),
              static_cast<double>(g_drv.best));
    ++g_drv.lines;
}
// a new drive replaces a running one (that one's motor settings go back first)
inline void DriveBegin(DriveCtl &c, const Drive &d) {
    if (c.on) DriveStop(c, "replaced by a new drive");
    c.d = d;
    InterlockedExchange(&c.on, 1);
}

}  // namespace tlact
