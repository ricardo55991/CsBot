using System;
using System.Reflection;
using System.Linq;

var asm = Assembly.LoadFrom(@"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\api\CounterStrikeSharp.API.dll");
var types = asm.GetTypes();
Console.WriteLine("Total types: " + types.Length);
var relevant = types.Where(t => t.Name.Contains("Timer") || t.Name.Contains("Command") || t.Name.Contains("CsTeam") || t.Name.Contains("RoundEndReason"));
foreach (var t in relevant)
{
    Console.WriteLine(t.FullName);
}
