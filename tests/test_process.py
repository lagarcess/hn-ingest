from hn_ingest.process import (
    classify_type,
    extract_domain,
    normalize_time,
    process_item,
    score_bucket,
)


def test_classify_type_known_and_unknown():
    assert classify_type("story") == "story"
    assert classify_type("comment") == "comment"
    assert classify_type("job") == "job"
    assert classify_type("poll") == "poll"
    assert classify_type("pollopt") == "unknown"
    assert classify_type(None) == "unknown"
    assert classify_type("ask") == "unknown"


def test_extract_domain():
    assert extract_domain("http://www.getdropbox.com/u/2/screencast.html") == "getdropbox.com"
    assert extract_domain("https://example.com:443/path") == "example.com"
    assert extract_domain(None) is None
    assert extract_domain("") is None


def test_normalize_time_iso_utc():
    assert normalize_time(1175714200) == "2007-04-04T19:16:40Z"
    assert normalize_time(None) is None


def test_score_bucket_thresholds():
    assert score_bucket(None) == "none"
    assert score_bucket(0) == "low"
    assert score_bucket(49) == "low"
    assert score_bucket(50) == "mid"
    assert score_bucket(199) == "mid"
    assert score_bucket(200) == "high"


def test_process_item_derives_fields():
    processed = process_item(
        {
            "id": 8863,
            "type": "story",
            "time": 1175714200,
            "url": "http://www.getdropbox.com/u/2/screencast.html",
            "score": 111,
            "title": "Dropbox",
        }
    )
    assert processed["type"] == "story"
    assert processed["domain"] == "getdropbox.com"
    assert processed["time_iso"] == "2007-04-04T19:16:40Z"
    assert processed["score_bucket"] == "mid"
    assert processed["id"] == 8863
    assert processed["title"] == "Dropbox"
