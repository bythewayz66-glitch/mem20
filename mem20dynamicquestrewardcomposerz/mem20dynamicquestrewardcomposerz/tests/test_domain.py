import importlib
MOD="mem20dynamicquestrewardcomposerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_gen(): m=_m(); q=m.generate_quest(2,1); assert q["difficulty"]==2
def test_reward(): m=_m(); q=m.generate_quest(2,1); r=m.reward_for_quest(q,5); assert r["xp"]>0
def test_balance(): m=_m(); qs=[{"reward":10},{"reward":20}]; r=m.balance_quests(qs); assert "balanced" in r[0]
def test_chain(): m=_m(); qs=[{"difficulty":2},{"difficulty":1}]; r=m.quest_chain(qs); assert r[0]["difficulty"]==1
def test_rate(): m=_m(); assert m.completion_rate(7,10)==0.7
