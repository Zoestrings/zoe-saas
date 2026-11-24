Add-Type -AssemblyName System.Drawing
$bmp = [System.Drawing.Bitmap]::FromFile('C:\Users\GOODLUCK\.gemini\antigravity\brain\33d6fdb3-0ab6-4166-9c5d-8766922c0ea0\.user_uploaded\media_1795443722501_f7d5f292.jpg')

$minX = 1000; $maxX = 0; $minY = 1000; $maxY = 0;
for ($x=100; $x -lt 450; $x+=2) {
    for ($y=60; $y -lt 360; $y+=2) {
        $c = $bmp.GetPixel($x, $y)
        if ($c.R -gt 30 -or $c.G -gt 35 -or $c.B -gt 35) {
            if ($x -lt $minX) { $minX = $x }
            if ($x -gt $maxX) { $maxX = $x }
            if ($y -lt $minY) { $minY = $y }
            if ($y -gt $maxY) { $maxY = $y }
        }
    }
}
$w = $maxX - $minX
$h = $maxY - $minY
Write-Host "Mark Bounding Box: x=$minX..$maxX, y=$minY..$maxY, width=$w, height=$h"

$tMinX = 1000; $tMaxX = 0; $tMinY = 1000; $tMaxY = 0;
for ($x=400; $x -lt 850; $x+=2) {
    for ($y=60; $y -lt 420; $y+=2) {
        $c = $bmp.GetPixel($x, $y)
        if ($c.R -gt 30 -or $c.G -gt 35 -or $c.B -gt 35) {
            if ($x -lt $tMinX) { $tMinX = $x }
            if ($x -gt $tMaxX) { $tMaxX = $x }
            if ($y -lt $tMinY) { $tMinY = $y }
            if ($y -gt $tMaxY) { $tMaxY = $y }
        }
    }
}
$tw = $tMaxX - $tMinX
$th = $tMaxY - $tMinY
Write-Host "Text Bounding Box: x=$tMinX..$tMaxX, y=$tMinY..$tMaxY, width=$tw, height=$th"

$aMinX = 1000; $aMaxX = 0; $aMinY = 1000; $aMaxY = 0;
for ($x=40; $x -lt 250; $x+=2) {
    for ($y=370; $y -lt 550; $y+=2) {
        $c = $bmp.GetPixel($x, $y)
        if ($c.R -gt 30 -or $c.G -gt 35 -or $c.B -gt 35) {
            if ($x -lt $aMinX) { $aMinX = $x }
            if ($x -gt $aMaxX) { $aMaxX = $x }
            if ($y -lt $aMinY) { $aMinY = $y }
            if ($y -gt $aMaxY) { $aMaxY = $y }
        }
    }
}
$aw = $aMaxX - $aMinX
$ah = $aMaxY - $aMinY
Write-Host "App Icon Bounding Box: x=$aMinX..$aMaxX, y=$aMinY..$aMaxY, width=$aw, height=$ah"

$bmp.Dispose()
