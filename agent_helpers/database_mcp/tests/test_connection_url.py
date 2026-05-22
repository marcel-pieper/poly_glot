from database_mcp.connection_url import rewrite_host_port


def test_rewrite_postgresql_url():
    url = "postgresql://postgres:secret@localhost:5433/polyglot"
    assert (
        rewrite_host_port(url, "127.0.0.1", 15433)
        == "postgresql://postgres:secret@127.0.0.1:15433/polyglot"
    )


def test_rewrite_psycopg_driver_url():
    url = "postgresql+psycopg://postgres:postgres@127.0.0.1:5433/polyglot"
    assert (
        rewrite_host_port(url, "127.0.0.1", 19999)
        == "postgresql+psycopg://postgres:postgres@127.0.0.1:19999/polyglot"
    )
