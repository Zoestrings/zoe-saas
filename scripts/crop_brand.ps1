Add-Type -AssemblyName System.Drawing

$srcPath = "C:\Users\GOODLUCK\.gemini\antigravity\brain\33d6fdb3-0ab6-4166-9c5d-8766922c0ea0\.user_uploaded\media_1795443722501_f7d5f292.jpg"
$src = [System.Drawing.Image]::FromFile($srcPath)

function CropAndSave($x, $y, $w, $h, $dest) {
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
    Write-Host "Exported: $dest ($w x $h)"
}

# 1. 3D Ribbon 'Z' mark: x: 170, y: 130, w: 225, h: 225
CropAndSave 170 130 225 225 "saas-dashboard\frontend\public\zoe-mark.png"

# 2. App Icon (the rounded squircle box in lower left):
CropAndSave 55 375 150 160 "saas-dashboard\frontend\public\zoe-app-icon.png"

# 3. Favicon (64x64):
$appIcon = [System.Drawing.Image]::FromFile("saas-dashboard\frontend\public\zoe-app-icon.png")
$favBmp = New-Object System.Drawing.Bitmap 64, 64
$fg = [System.Drawing.Graphics]::FromImage($favBmp)
$fg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$fg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$fg.DrawImage($appIcon, 0, 0, 64, 64)
$favBmp.Save("saas-dashboard\frontend\public\favicon.png", [System.Drawing.Imaging.ImageFormat]::Png)
$fg.Dispose()
$favBmp.Dispose()
$appIcon.Dispose()
Write-Host "Exported: favicon.png (64x64)"

# 4. Full horizontal brand lockup:
CropAndSave 170 130 640 225 "saas-dashboard\frontend\public\zoe-brand-full.png"

$src.Dispose()
