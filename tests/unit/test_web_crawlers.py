from vectorvein.workflow.nodes import SocialMediaCrawler
from vectorvein.workflow.nodes.web_crawlers import (
    SOCIAL_MEDIA_ACTION_OPTIONS,
    SOCIAL_MEDIA_PLATFORM_OPTIONS,
)


ZHIHU_ACTIONS = {
    "fetch_column_articles": ("column_id", "limit", "offset"),
    "fetch_column_article_detail": ("article_id",),
    "fetch_article_search_v3": (
        "keyword",
        "offset",
        "limit",
        "show_all_topics",
        "search_source",
        "search_hash_id",
        "vertical",
        "sort",
        "time_interval",
        "vertical_info",
    ),
    "fetch_user_search_v3": ("keyword", "offset", "limit"),
    "fetch_topic_search_v3": ("keyword", "offset", "limit"),
    "fetch_answer_detail": ("answer_id",),
    "fetch_comment_v5": ("answer_id", "order_by", "limit", "offset"),
    "fetch_user_info": ("user_url_token",),
    "fetch_user_articles": ("user_url_token", "offset", "limit", "sort_type"),
    "fetch_question_answers": ("question_id", "cursor", "limit", "offset", "order", "session_id"),
}


def test_social_media_crawler_exposes_generic_runtime_ports():
    crawler = SocialMediaCrawler(id="zhihu-crawler")
    data = crawler.to_dict()

    assert data["type"] == "SocialMediaCrawler"
    assert data["category"] == "webCrawlers"
    assert data["data"]["task_name"] == "web_crawlers.social_media_crawler"
    assert {"platform", "action", "params", "requests", "output_format", "fail_on_error"}.issubset(
        data["data"]["template"]
    )
    assert data["data"]["template"]["output"]["is_output"] is True
    assert data["data"]["template"]["output_raw_data"]["is_output"] is True


def test_social_media_crawler_includes_zhihu_actions_and_parameters():
    crawler = SocialMediaCrawler()
    ports = crawler.ports
    action_values = {item["value"] for item in SOCIAL_MEDIA_ACTION_OPTIONS}

    assert {item["value"] for item in SOCIAL_MEDIA_PLATFORM_OPTIONS} >= {"zhihu"}
    assert set(ZHIHU_ACTIONS) <= action_values
    for action, parameters in ZHIHU_ACTIONS.items():
        assert action in action_values
        assert set(parameters) <= ports.keys()

    assert ports["show_all_topics"].value == "0"
    assert {item["value"] for item in ports["show_all_topics"].options} == {"0", "1"}
    assert {item["value"] for item in ports["search_source"].options} == {"Normal", "Filter"}
    assert {item["value"] for item in ports["vertical"].options} == {"", "answer", "article", "zvideo"}
    assert {item["value"] for item in ports["order_by"].options} == {"score", "ts"}
    assert {item["value"] for item in ports["sort_type"].options} == {"created", "voteups"}
    assert {item["value"] for item in ports["order"].options} == {"default", "updated"}


def test_social_media_crawler_accepts_zhihu_configuration():
    crawler = SocialMediaCrawler()
    crawler.ports["platform"].value = "zhihu"
    crawler.ports["action"].value = "fetch_question_answers"
    crawler.ports["question_id"].value = "123"
    crawler.ports["params"].value = {"question_id": "123", "limit": 5}

    assert crawler.ports["platform"].value == "zhihu"
    assert crawler.ports["action"].value == "fetch_question_answers"
    assert crawler.ports["params"].value == {"question_id": "123", "limit": 5}


def test_social_media_crawler_accepts_zhihu_answer_detail_configuration():
    crawler = SocialMediaCrawler()
    crawler.ports["platform"].value = "zhihu"
    crawler.ports["action"].value = "fetch_answer_detail"
    crawler.ports["answer_id"].value = "456"

    assert crawler.ports["action"].value == "fetch_answer_detail"
    assert crawler.ports["answer_id"].value == "456"


def test_social_media_crawler_preserves_zhihu_comment_contract():
    crawler = SocialMediaCrawler()

    crawler.ports["platform"].value = "zhihu"
    crawler.ports["action"].value = "fetch_comment_v5"
    crawler.ports["answer_id"].value = "456"
    crawler.ports["order_by"].value = "ts"
    crawler.ports["limit"].value = "20"
    crawler.ports["offset"].value = "5"

    assert {
        name: crawler.ports[name].value
        for name in ("answer_id", "order_by", "limit", "offset")
    } == {
        "answer_id": "456",
        "order_by": "ts",
        "limit": "20",
        "offset": "5",
    }
