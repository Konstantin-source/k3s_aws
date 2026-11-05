# fuehrt alle experimente mehrfach aus und sichert die rohdaten pro lauf
$env:PYTHONUTF8 = "1"
$res = "experiments/results"
$kc = "--kubeconfig ./kubeconfig-aws.yaml"

function Wait-Healthy {
    for ($i = 0; $i -lt 60; $i++) {
        $h = kubectl --kubeconfig ./kubeconfig-aws.yaml get application -n argocd resilience-lab -o jsonpath="{.status.health.status}" 2>$null
        $s = kubectl --kubeconfig ./kubeconfig-aws.yaml get application -n argocd resilience-lab -o jsonpath="{.status.sync.status}" 2>$null
        if ($h -eq "Healthy" -and $s -eq "Synced") { return }
        Start-Sleep 5
    }
}

foreach ($n in 1..3) {
    Wait-Healthy; Start-Sleep 20
    python experiments/scripts/run-exp2-bad-deploy.py
    New-Item -ItemType Directory -Force "$res/run$n" | Out-Null
    Copy-Item "$res/exp2-*" "$res/run$n/" -Force
    Wait-Healthy; Start-Sleep 20
    python experiments/scripts/run-exp1-crash.py
    Copy-Item "$res/exp1-*" "$res/run$n/" -Force
    Wait-Healthy; Start-Sleep 20
    python experiments/scripts/run-exp3-drift.py
    Copy-Item "$res/exp3-*" "$res/run$n/" -Force
}
"BATCH_DONE"
