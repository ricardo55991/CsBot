with open(r'src/CsBotManager/MicroMoveEngine.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the wrongly placed stationary block in BuildFogOfWarInputTensorForTeam
bad_block = """            bool isStationary = false;
            if (_stationaryTrackers.TryGetValue(bot.Slot, out var stPosTime))
            {
                float dX = curX - stPosTime.Pos.X;
                float dY = curY - stPosTime.Pos.Y;
                float dZ = curZ - stPosTime.Pos.Z;
                float distMoved = MathF.Sqrt(dX * dX + dY * dY + dZ * dZ);
                if (distMoved > 50.0f)
                {
                    _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);
                }
                else if ((currentTime - stPosTime.SinceTime) > 3.0f)
                {
                    isStationary = true;
                }
            }
            else
            {
                _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);
            }"""

bad_block_crlf = bad_block.replace('\n', '\r\n')
if bad_block_crlf in text:
    text = text.replace(bad_block_crlf, '', 1)
elif bad_block in text:
    text = text.replace(bad_block, '', 1)
else:
    print('Warning: bad_block not found')

# 2. Add isStationary block inside PredictBatch16Hz right after weaponName
target_in_loop = """            float speed2D = MathF.Sqrt(vx * vx + vy * vy);
            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";"""

rep_in_loop = """            float speed2D = MathF.Sqrt(vx * vx + vy * vy);
            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";

            // Rastreia se o bot TR esta travado no mesmo raio de 50u ha mais de 3.0s (Correcao 1B)
            bool isStationary = false;
            if (_stationaryTrackers.TryGetValue(bot.Slot, out var stPosTime))
            {
                float dX = curX - stPosTime.Pos.X;
                float dY = curY - stPosTime.Pos.Y;
                float dZ = curZ - stPosTime.Pos.Z;
                float distMoved = MathF.Sqrt(dX * dX + dY * dY + dZ * dZ);
                if (distMoved > 50.0f)
                {
                    _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);
                }
                else if ((currentTime - stPosTime.SinceTime) > 3.0f)
                {
                    isStationary = true;
                }
            }
            else
            {
                _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);
            }"""

target_in_loop_crlf = target_in_loop.replace('\n', '\r\n')
rep_in_loop_crlf = rep_in_loop.replace('\n', '\r\n')

if target_in_loop_crlf in text:
    text = text.replace(target_in_loop_crlf, rep_in_loop_crlf, 1)
elif target_in_loop in text:
    text = text.replace(target_in_loop, rep_in_loop, 1)
else:
    raise AssertionError('target_in_loop not found')

with open(r'src/CsBotManager/MicroMoveEngine.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed MicroMoveEngine.cs successfully')
