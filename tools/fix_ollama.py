with open(r'src/CsBotManager/OllamaIglService.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the broken lines 324-326
broken = '''        bool isCt = team == CsTeam.CounterTerrorist;
        string reasonClean = string.IsNullOrEmpty(reason) ? "Deterministic Rule" : reason.Replace(""", "'").Replace("", " ").Replace("
", " ");
        var plan = new TacticalPlan'''

fixed = '''        bool isCt = team == CsTeam.CounterTerrorist;
        string reasonClean = string.IsNullOrEmpty(reason) ? "Deterministic Rule" : reason.Replace('"', '\'').Replace('\\r', ' ').Replace('\\n', ' ');
        var plan = new TacticalPlan'''

broken_crlf = broken.replace('\n', '\r\n')
fixed_crlf = fixed.replace('\n', '\r\n')

if broken_crlf in text:
    text = text.replace(broken_crlf, fixed_crlf, 1)
elif broken in text:
    text = text.replace(broken, fixed, 1)
else:
    # let's find reasonClean line
    import re
    text = re.sub(r'string reasonClean = [^\n]+\n[^\n]+\n', 'string reasonClean = string.IsNullOrEmpty(reason) ? "Deterministic Rule" : reason.Replace(\'"\', \'\\\'\').Replace(\'\\r\', \' \').Replace(\'\\n\', \' \');\r\n', text)

with open(r'src/CsBotManager/OllamaIglService.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed successfully')
