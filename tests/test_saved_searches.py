from __future__ import annotations

from freightline.storage.saved_searches import DEFAULT_SHARE_TOKEN, SavedSearchRepository


def make_repo(conn) -> SavedSearchRepository:
    return SavedSearchRepository(conn)


def test_create_and_get(conn):
    repo = make_repo(conn)
    saved = repo.create(
        name="Open exceptions", filter_expression="status = 'exception'", owner="ops"
    )
    assert repo.get(saved.id).name == "Open exceptions"


def test_get_returns_none_when_absent(conn):
    assert make_repo(conn).get(999) is None


def test_list_is_sorted_by_name(conn):
    repo = make_repo(conn)
    repo.create(name="Zulu", filter_expression="status = 'delivered'", owner="ops")
    repo.create(name="Alpha", filter_expression="status = 'created'", owner="ops")
    assert [item.name for item in repo.list_all()] == ["Alpha", "Zulu"]


def test_run_returns_matching_shipments(conn, service, quote_request):
    service.create_shipment(quote_request, reference="PO-1")
    repo = make_repo(conn)
    saved = repo.create(name="Atlas", filter_expression="carrier_code = 'atlas'", owner="ops")
    assert len(repo.run(saved.id)) == 1


def test_run_on_a_missing_search_is_empty(conn):
    assert make_repo(conn).run(4242) == []


def test_delete_with_the_share_token(conn):
    repo = make_repo(conn)
    saved = repo.create(name="Temp", filter_expression="status = 'created'", owner="ops")
    assert repo.delete(saved.id, DEFAULT_SHARE_TOKEN) is True
    assert repo.get(saved.id) is None


def test_delete_without_the_share_token(conn):
    repo = make_repo(conn)
    saved = repo.create(name="Temp", filter_expression="status = 'created'", owner="ops")
    assert repo.delete(saved.id, "wrong") is False
    assert repo.get(saved.id) is not None
