Add-Type -AssemblyName System.Drawing

$srcPath = "C:\Users\GOODLUCK\.gemini\antigravity\brain\33d6fdb3-0ab6-4166-9c5d-8766922c0ea0\.user_uploaded\media_1795443722501_f7d5f292.jpg"
$src = [System.Drawing.Bitmap]::FromFile($srcPath)

function CropWithSmoothAlpha($x, $y, $w, $h, $dest) {
    $bmp = New-Object System.Drawing.Bitmap $w, $h, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    
    for ($j = 0; $j -lt $h; $j++) {
        for ($i = 0; $i -lt $w; $i++) {
            $sx = $x + $i
            $sy = $y + $j
            if ($sx -ge 0 -and $sx -lt $src.Width -and $sy -ge 0 -and $sy -lt $src.Height) {
                $c = $src.GetPixel($sx, $sy)
                
                # Estimate background level
                # Dark ambient background has R~0-3, G~8-14, B~10-16
                $excessR = [Math]::Max(0, [int]$c.R - 2)
                $excessG = [Math]::Max(0, [int]$c.G - 14)
                $excessB = [Math]::Max(0, [int]$c.B - 16)
                $val = [Math]::Max($excessR, [Math]::Max($excessG, $excessB))
                
                if ($val -le 4) {
                    $bmp.SetPixel($i, $j, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
                } elseif ($val -le 28) {
                    $alpha = [int](($val - 4) / 24.0 * 255.0)
                    $bmp.SetPixel($i, $j, [System.Drawing.Color]::FromArgb($alpha, $c.R, $c.G, $c.B))
                } else {
                    $bmp.SetPixel($i, $j, [System.Drawing.Color]::FromArgb(255, $c.R, $c.G, $c.B))
                }
            }
        }
    }
    
    $bmp.Save($dest, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "Generated: $dest ($w x $h)"
}

function CropDirect($x, $y, $w, $h, $dest) {
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $rect = New-Object System.Drawing.Rectangle $x, $y, $w, $h
    $destRect = New-Object System.Drawing.Rectangle 0, 0, $w, $h
    $g.DrawImage($src, $destRect, $rect, [System.Drawing.GraphicsUnit]::Pixel)
    $bmp.Save($dest, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
    Write-Host "Generated Direct: $dest ($w x $h)"
}

# 1. 3D Ribbon 'Z' Mark with mint star sparkle
# Bounds: x=180..395 (w=215), y=80..275 (h=195)
# Add 3px margin
CropWithSmoothAlpha 178 78 220 200 "saas-dashboard\frontend\public\zoe-mark.png"

# 2. Complete Horizontal Brand Lockup (Ribbon Z + Zoe + INTELLIGENCE)
# Bounds: x=178..805 (w=627), y=78..288 (h=210)
CropWithSmoothAlpha 178 78 630 212 "saas-dashboard\frontend\public\zoe-brand-full.png"
CropDirect 178 78 630 212 "saas-dashboard\frontend\public\zoe-full-logo.png"

# 3. Squircle App Icon
CropDirect 55 376 150 162 "saas-dashboard\frontend\public\zoe-app-icon.png"

# 4. Favicon (64x64) from app icon
$appIcon = [System.Drawing.Image]::FromFile("saas-dashboard\frontend\public\zoe-app-icon.png")
$favBmp = New-Object System.Drawing.Bitmap 64, 64
$fg = [System.Drawing.Graphics]::FromImage($favBmp)
$fg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$fg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$fg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$fg.DrawImage($appIcon, 0, 0, 64, 64)
$favBmp.Save("saas-dashboard\frontend\public\favicon.png", [System.Drawing.Imaging.ImageFormat]::Png)
$fg.Dispose()
$favBmp.Dispose()
$appIcon.Dispose()

# 5. Monochrome White Mark
CropWithSmoothAlpha 455 410 98 120 "saas-dashboard\frontend\public\zoe-monochrome.png"

$src.Dispose()
Write-Host "Done! All official brand assets created."
