using System;
using System.Reflection;
using System.Linq;

var asm = Assembly.LoadFrom(@"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\api\CounterStrikeSharp.API.dll");
var t = asm.GetType("CounterStrikeSharp.API.Core.PlayerConnectedState");
if (t != null)
{
    foreach (var name in Enum.GetNames(t))
    {
        Console.WriteLine("PlayerConnectedState: " + name);
    }
}
var chatColors = asm.GetType("CounterStrikeSharp.API.Modules.Utils.ChatColors");
if (chatColors != null)
{
    foreach (var f in chatColors.GetFields())
    {
        Console.WriteLine("ChatColors: " + f.Name);
    }
}
