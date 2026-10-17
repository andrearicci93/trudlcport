# usage: vm_sendkey.ps1 -Scan 0x42 [-Vk 0x77]   (sends key down/up with hardware scan code; F8 = vk 0x77 scan 0x42)
param([int]$Vk = 0x77, [int]$Scan = 0x42)
Add-Type @"
using System; using System.Runtime.InteropServices;
public class K { [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint fl, UIntPtr ex); }
"@
[K]::keybd_event([byte]$Vk, [byte]$Scan, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 120
[K]::keybd_event([byte]$Vk, [byte]$Scan, 2, [UIntPtr]::Zero)
