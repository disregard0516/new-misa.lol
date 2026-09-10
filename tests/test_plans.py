from app.core.plans import gate_profile, plan_rank


def test_ranks():
    assert plan_rank(None) == 0 and plan_rank("Lifetime") == 1 and plan_rank("supporter") == 2
    assert plan_rank("premium") == 1          # unknown paid plans count as lifetime-level


def test_gating_table():
    cfg = {"settings": {"usernameEffect": "Glow", "usernameGlow": True}, "assets": {"cursor": {"url": "/u/x/c.png"}}}
    assert set(gate_profile(cfg, "free")) == {"settings.usernameEffect", "settings.usernameGlow", "assets.cursor.url"}
    assert cfg["settings"]["usernameEffect"] == "None"
    cfg = {"settings": {"usernameEffect": "Glow"}}
    assert gate_profile(cfg, "lifetime") == []
