# Toggle to control whether to return the raw API response
$RETURN_RAW_API_RESPONSE = $false

function Extract-Patterns {
    param (
        [string]$Text,
        [hashtable]$Patterns
    )
    $Result = @{}
    foreach ($Key in $Patterns.Keys) {
        $Pattern, $Func = $Patterns[$Key]
        $Match = [regex]::Match($Text, $Pattern)
        if ($Match.Success) {
            $Result[$Key] = & $Func $Match
            $Text = $Text -replace $Pattern, ''
        }
    }
    $Result['text'] = $Text.Trim()
    return $Result
}

function Invoke-APICall {
    $Url = "https://api.pons.com/v1/dictionary?l=bgen&q=искам"
    $Headers = @{
        "X-Secret" = "XXX"
    }
    $Response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Get

    if ($RETURN_RAW_API_RESPONSE) {
        if ($Response.StatusCode -eq 200) {
            $Response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 4
        } else {
            Write-Output "Error: Received status code $($Response.StatusCode)"
        }
        return
    }

    if ($Response.StatusCode -eq 200) {
        $ResponseJson = $Response.Content | ConvertFrom-Json
        $Result = @()

        foreach ($LangEntry in $ResponseJson) {
            $LangData = @{
                lang = $LangEntry.lang
                hits = @()
            }

            foreach ($Hit in $LangEntry.hits) {
                $HitData = @{
                    type = $Hit.type
                    opendict = $Hit.opendict
                    roms = @()
                }

                foreach ($Rom in $Hit.roms) {
                    $RomData = @{
                        headword = $Rom.headword
                        headword_full = $Rom.headword_full
                        wordclass = $Rom.wordclass
                        conjugation = ""
                        verbclass = ""
                        arabs = @()
                    }

                    $HeadwordFull = $Rom.headword_full
                    $Patterns = @{
                        conjugation = { param($Match) $Match.Groups[1].Value } = '<span class=\\?"conjugation\\?"><acronym title=\\?"([^<][a-z ]+)\\?">[^<][a-z]+</acronym></span>'
                        wordclass = { param($Match) $Match.Groups[1].Value } = '<span class=\\?"wordclass\\?">([^<][a-zA-Z ]+)</span>'
                        verbclass = { param($Match) $Match.Groups[1].Value } = '<span class=\\?"verbclass\\?"><acronym title=\\?"([^<][a-zA-Z ]+)\\?">[^<][a-z]+</acronym></span>'
                    }

                    $ExtractedData = Extract-Patterns -Text $HeadwordFull -Patterns $Patterns
                    $RomData += $ExtractedData
                    $RomData['headword_full'] = $ExtractedData['text']

                    foreach ($Arab in $Rom.arabs) {
                        $ArabData = @{
                            header = $Arab.header
                            sense = ""
                            entrynumber = ""
                            reflection = ""
                            translations = @()
                        }

                        $Header = $Arab.header
                        $Patterns = @{
                            entrynumber = { param($Match) $Match.Groups[0].Value } = '^\d\.'
                            sense = { param($Match) $Match.Groups[1].Value } = '<span class=\\?"sense\\?">\(?(.*?)\)?</span>'
                            reflection = { param($Match) $Match.Groups[1].Value } = '<span class=\\?"reflection\\?">\(?(.*?)\)?</span>'
                        }

                        $ExtractedData = Extract-Patterns -Text $Header -Patterns $Patterns
                        $ArabData += $ExtractedData
                        $ArabData['header'] = $ExtractedData['text']

                        foreach ($Translation in $Arab.translations) {
                            $TranslationData = @{
                                source = $Translation.source
                                target = $Translation.target
                            }

                            $ExtractedData = Extract-Patterns -Text $TranslationData['source'] -Patterns $Patterns
                            $TranslationData += $ExtractedData
                            $TranslationData['source'] = $ExtractedData['text']

                            $ArabData.translations += $TranslationData
                        }

                        $RomData.arabs += $ArabData
                    }

                    $HitData.roms += $RomData
                }

                $LangData.hits += $HitData
            }

            $Result += $LangData
        }

        $Result | ConvertTo-Json -Depth 4
    } else {
        Write-Output "Error: Received status code $($Response.StatusCode)"
    }
}

Invoke-APICall