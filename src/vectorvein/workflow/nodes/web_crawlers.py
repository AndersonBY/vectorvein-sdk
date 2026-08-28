from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


SOCIAL_MEDIA_PLATFORM_OPTIONS = [
    {"value": "douyin", "label": "Douyin"},
    {"value": "instagram", "label": "Instagram"},
    {"value": "linkedin", "label": "LinkedIn"},
    {"value": "kuaishou", "label": "Kuaishou"},
    {"value": "weixin_mp", "label": "WeChat MP"},
    {"value": "weibo", "label": "Weibo"},
    {"value": "twitter", "label": "Twitter"},
    {"value": "tiktok", "label": "TikTok"},
    {"value": "xiaohongshu", "label": "Xiaohongshu"},
    {"value": "zhihu", "label": "Zhihu"},
]

SOCIAL_MEDIA_ACTION_OPTIONS = [
    {"value": action, "label": action}
    for action in (
        "general_search_v3",
        "hot_search_list",
        "user_info",
        "user_posts",
        "video",
        "video_comments",
        "search_users",
        "search_locations",
        "location_posts",
        "post_info",
        "company_profile",
        "company_posts",
        "company_jobs",
        "company_people",
        "user_profile",
        "user_contact",
        "search_jobs",
        "search_people",
        "hot_list",
        "user_hot_post",
        "search_comprehensive",
        "article_detail_json",
        "article_comment_list",
        "article_list",
        "hot_search_summary",
        "realtime_search",
        "post_comments",
        "search_user_posts",
        "search",
        "user_tweets",
        "video_search",
        "search_ads",
        "ads_detail",
        "keyword_insights",
        "creator_list",
        "search_creators",
        "popular_trends",
        "fake_view_analysis",
        "video_metrics",
        "comment_keywords",
        "trending_searchwords",
        "note_info",
        "note_comments",
        "notes_by_topic",
        "search_notes",
        "user_notes",
        "fetch_column_articles",
        "fetch_column_article_detail",
        "fetch_article_search_v3",
        "fetch_user_search_v3",
        "fetch_topic_search_v3",
        "fetch_comment_v5",
        "fetch_user_info",
        "fetch_user_articles",
        "fetch_question_answers",
    )
]


class SocialMediaCrawler(Node):
    """Request data from the registered TikHub social-media actions."""

    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="SocialMediaCrawler",
            category="webCrawlers",
            task_name="web_crawlers.social_media_crawler",
            description="Request social-media data through a platform action.",
            node_id=id,
            ports={
                "platform": InputPort(
                    name="platform",
                    port_type=PortType.SELECT,
                    value="",
                    options=SOCIAL_MEDIA_PLATFORM_OPTIONS,
                    required=False,
                ),
                "action": InputPort(
                    name="action",
                    port_type=PortType.SELECT,
                    value="",
                    options=SOCIAL_MEDIA_ACTION_OPTIONS,
                    required=False,
                ),
                "column_id": InputPort(name="column_id", port_type=PortType.INPUT, value="", required=False),
                "article_id": InputPort(name="article_id", port_type=PortType.INPUT, value="", required=False),
                "keyword": InputPort(name="keyword", port_type=PortType.INPUT, value="", required=False),
                "offset": InputPort(name="offset", port_type=PortType.INPUT, value="", required=False),
                "limit": InputPort(name="limit", port_type=PortType.INPUT, value="", required=False),
                "show_all_topics": InputPort(
                    name="show_all_topics",
                    port_type=PortType.SELECT,
                    value="0",
                    options=[
                        {"value": "0", "label": "0 (Do not show topics)"},
                        {"value": "1", "label": "1 (Show topics)"},
                    ],
                    required=False,
                ),
                "search_source": InputPort(
                    name="search_source",
                    port_type=PortType.SELECT,
                    value="Normal",
                    options=[
                        {"value": "Normal", "label": "Normal"},
                        {"value": "Filter", "label": "Filter"},
                    ],
                    required=False,
                ),
                "search_hash_id": InputPort(name="search_hash_id", port_type=PortType.INPUT, value="", required=False),
                "vertical": InputPort(
                    name="vertical",
                    port_type=PortType.SELECT,
                    value="",
                    options=[
                        {"value": "", "label": "Any"},
                        {"value": "answer", "label": "Answers"},
                        {"value": "article", "label": "Articles"},
                        {"value": "zvideo", "label": "Videos"},
                    ],
                    required=False,
                ),
                "sort": InputPort(
                    name="sort",
                    port_type=PortType.SELECT,
                    value="",
                    options=[
                        {"value": "", "label": "Comprehensive"},
                        {"value": "upvoted_count", "label": "Most upvoted"},
                        {"value": "created_time", "label": "Latest"},
                    ],
                    required=False,
                ),
                "time_interval": InputPort(
                    name="time_interval",
                    port_type=PortType.SELECT,
                    value="",
                    options=[
                        {"value": "", "label": "Any time"},
                        {"value": "a_day", "label": "Within a day"},
                        {"value": "a_week", "label": "Within a week"},
                        {"value": "a_month", "label": "Within a month"},
                        {"value": "three_months", "label": "Within three months"},
                        {"value": "half_a_year", "label": "Within half a year"},
                        {"value": "a_year", "label": "Within a year"},
                    ],
                    required=False,
                ),
                "vertical_info": InputPort(name="vertical_info", port_type=PortType.INPUT, value="", required=False),
                "answer_id": InputPort(name="answer_id", port_type=PortType.INPUT, value="", required=False),
                "order_by": InputPort(
                    name="order_by",
                    port_type=PortType.SELECT,
                    value="score",
                    options=[
                        {"value": "score", "label": "Hottest"},
                        {"value": "ts", "label": "Latest"},
                    ],
                    required=False,
                ),
                "user_url_token": InputPort(name="user_url_token", port_type=PortType.INPUT, value="", required=False),
                "sort_type": InputPort(
                    name="sort_type",
                    port_type=PortType.SELECT,
                    value="created",
                    options=[
                        {"value": "created", "label": "Latest"},
                        {"value": "voteups", "label": "Most upvoted"},
                    ],
                    required=False,
                ),
                "question_id": InputPort(name="question_id", port_type=PortType.INPUT, value="", required=False),
                "cursor": InputPort(name="cursor", port_type=PortType.INPUT, value="", required=False),
                "order": InputPort(
                    name="order",
                    port_type=PortType.SELECT,
                    value="default",
                    options=[
                        {"value": "default", "label": "Default"},
                        {"value": "updated", "label": "Latest"},
                    ],
                    required=False,
                ),
                "session_id": InputPort(name="session_id", port_type=PortType.INPUT, value="", required=False),
                "params": InputPort(
                    name="params",
                    port_type=PortType.TEXTAREA,
                    value={},
                    field_type="dict",
                    required=False,
                ),
                "requests": InputPort(
                    name="requests",
                    port_type=PortType.TEXTAREA,
                    value=[],
                    field_type="list",
                    required=False,
                ),
                "output_format": InputPort(
                    name="output_format",
                    port_type=PortType.SELECT,
                    value="markdown",
                    options=[
                        {"value": "markdown", "label": "Markdown"},
                        {"value": "data", "label": "Data"},
                        {"value": "raw", "label": "Raw Data"},
                        {"value": "envelope", "label": "Response Envelope"},
                    ],
                    required=False,
                ),
                "fail_on_error": InputPort(
                    name="fail_on_error",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "output": OutputPort(name="output", field_type="str|dict"),
                "output_raw_data": OutputPort(name="output_raw_data", field_type="str|dict"),
            },
        )


class BilibiliCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="BilibiliCrawler",
            category="webCrawlers",
            task_name="web_crawlers.bilibili_crawler",
            node_id=id,
            ports={
                "url_or_bvid": InputPort(
                    name="url_or_bvid",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "download_video": InputPort(
                    name="download_video",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="str",
                    options=[{"value": "str", "label": "str"}, {"value": "list", "label": "list"}],
                    required=False,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_subtitle": OutputPort(name="output_subtitle"),
                "output_video": OutputPort(
                    name="output_video",
                    condition="return fieldsData.download_video.value",
                    condition_python=lambda ports: ports["download_video"].value,
                ),
            },
        )


class DouyinCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="DouyinCrawler",
            category="webCrawlers",
            task_name="web_crawlers.douyin_crawler",
            node_id=id,
            ports={
                "url": InputPort(
                    name="url",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_video": OutputPort(name="output_video"),
                "output_audio": OutputPort(name="output_audio"),
            },
        )


class TextCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="TextCrawler",
            category="webCrawlers",
            task_name="web_crawlers.text_crawler",
            node_id=id,
            ports={
                "url": InputPort(
                    name="url",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "html", "label": "HTML"}],
                    required=False,
                ),
                "use_oversea_crawler": InputPort(
                    name="use_oversea_crawler",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "advanced_mode": InputPort(
                    name="advanced_mode",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "remove_image": InputPort(
                    name="remove_image",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_text": OutputPort(name="output_text"),
            },
        )


class UniversalCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="UniversalCrawler",
            category="webCrawlers",
            task_name="web_crawlers.universal_crawler",
            node_id=id,
            ports={
                "url": InputPort(
                    name="url",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_video": OutputPort(name="output_video"),
                "output_audio": OutputPort(name="output_audio"),
            },
        )


class YoutubeCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="YoutubeCrawler",
            category="webCrawlers",
            task_name="web_crawlers.youtube_crawler",
            node_id=id,
            ports={
                "url_or_video_id": InputPort(
                    name="url_or_video_id",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "get_comments": InputPort(
                    name="get_comments",
                    port_type=PortType.CHECKBOX,
                    value=False,
                ),
                "comments_type": InputPort(
                    name="comments_type",
                    port_type=PortType.RADIO,
                    value="text_only",
                    options=[{"value": "text_only", "label": "text_only"}, {"value": "detailed", "label": "detailed"}],
                    condition="return fieldsData.get_comments.value",
                    condition_python=lambda ports: ports["get_comments"].value,
                ),
                "subtitle_format": InputPort(
                    name="subtitle_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "text"}, {"value": "srt", "label": "srt"}],
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="str",
                    options=[{"value": "str", "label": "str"}, {"value": "list", "label": "list"}],
                    required=False,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_subtitle": OutputPort(name="output_subtitle"),
                "output_comments": OutputPort(
                    name="output_comments",
                    condition="return fieldsData.get_comments.value",
                    condition_python=lambda ports: ports["get_comments"].value,
                ),
            },
        )
