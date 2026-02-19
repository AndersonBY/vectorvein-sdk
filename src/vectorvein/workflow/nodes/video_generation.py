from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class CogVideoX(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="CogVideoX",
            category="videoGeneration",
            task_name="video_generation.cog_video_x",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                    has_tooltip=True,
                ),
                "image": InputPort(
                    name="image",
                    port_type=PortType.FILE,
                    value=[],
                    required=False,
                    has_tooltip=True,
                    support_file_types=[".jpg", ".jpeg", ".png"],
                ),
                "auto_crop": InputPort(
                    name="auto_crop",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    has_tooltip=True,
                ),
                "model": InputPort(
                    name="model",
                    port_type=PortType.SELECT,
                    value="cogvideox",
                    options=[{"value": "cogvideox", "label": "cogvideox"}],
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="only_link",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class KlingVideo(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="KlingVideo",
            category="videoGeneration",
            task_name="video_generation.kling_video",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                    has_tooltip=True,
                ),
                "image": InputPort(
                    name="image",
                    port_type=PortType.FILE,
                    value=[],
                    required=False,
                    support_file_types=[".jpg", ".jpeg", ".png"],
                ),
                "duration": InputPort(
                    name="duration",
                    port_type=PortType.SELECT,
                    value=5,
                    options=[{"value": 5, "label": "5"}, {"value": 10, "label": "10"}],
                    required=False,
                ),
                "aspect_ratio": InputPort(
                    name="aspect_ratio",
                    port_type=PortType.SELECT,
                    value="16:9",
                    options=[{"value": "16:9", "label": "16:9"}, {"value": "9:16", "label": "9:16"}, {"value": "1:1", "label": "1:1"}],
                    required=False,
                ),
                "model": InputPort(
                    name="model",
                    port_type=PortType.SELECT,
                    value="v2_6_pro",
                    options=[
                        {"value": "v2_6_pro", "label": "v2_6_pro"},
                        {"value": "v2_1_master", "label": "v2_1_master"},
                        {"value": "v1_pro", "label": "v1_pro"},
                        {"value": "v1_standard", "label": "v1_standard"},
                    ],
                ),
                "generate_audio": InputPort(
                    name="generate_audio",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                    condition='return fieldsData.model.value === "v2_6_pro"',
                    condition_python=lambda ports: ports["model"].value == "v2_6_pro",
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="only_link",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class OmniHuman(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="OmniHuman",
            category="videoGeneration",
            task_name="video_generation.omni_human",
            node_id=id,
            ports={
                "image": InputPort(
                    name="image",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    has_tooltip=True,
                    support_file_types=[".jpg", ".jpeg", ".png"],
                ),
                "audio": InputPort(
                    name="audio",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    has_tooltip=True,
                    support_file_types=[".mp3", ".wav"],
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="only_link",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class SoraVideo(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="SoraVideo",
            category="videoGeneration",
            task_name="video_generation.sora_video",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                    has_tooltip=True,
                ),
                "image": InputPort(
                    name="image",
                    port_type=PortType.FILE,
                    value=[],
                    required=False,
                    support_file_types=[".jpg", ".jpeg", ".png"],
                ),
                "api_source": InputPort(
                    name="api_source",
                    port_type=PortType.SELECT,
                    value="low_cost",
                    options=[{"value": "low_cost", "label": "low_cost"}, {"value": "original", "label": "original_api"}],
                ),
                "low_cost_model": InputPort(
                    name="low_cost_model",
                    port_type=PortType.SELECT,
                    value="sora-2",
                    options=[{"value": "sora-2", "label": "sora-2"}, {"value": "sora-2-pro", "label": "sora-2-pro"}],
                    required=False,
                    condition='return fieldsData.api_source.value === "low_cost"',
                    condition_python=lambda ports: ports["api_source"].value == "low_cost",
                ),
                "aspect_ratio": InputPort(
                    name="aspect_ratio",
                    port_type=PortType.SELECT,
                    value="16:9",
                    options=[{"value": "16:9", "label": "16:9"}, {"value": "9:16", "label": "9:16"}],
                    required=False,
                    condition='return fieldsData.api_source.value === "low_cost"',
                    condition_python=lambda ports: ports["api_source"].value == "low_cost",
                ),
                "duration": InputPort(
                    name="duration",
                    port_type=PortType.SELECT,
                    value="10",
                    options=[{"value": "10", "label": "10s"}, {"value": "15", "label": "15s"}, {"value": "25", "label": "25s (sora-2-pro)"}],
                    required=False,
                    condition='return fieldsData.api_source.value === "low_cost"',
                    condition_python=lambda ports: ports["api_source"].value == "low_cost",
                ),
                "hd": InputPort(
                    name="hd",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                    condition='return fieldsData.api_source.value === "low_cost" && fieldsData.low_cost_model.value === "sora-2-pro"',
                    condition_python=lambda ports: ports["api_source"].value == "low_cost" and ports["low_cost_model"].value == "sora-2-pro",
                ),
                "seconds": InputPort(
                    name="seconds",
                    port_type=PortType.SELECT,
                    value=4,
                    options=[{"value": 4, "label": "4"}, {"value": 8, "label": "8"}, {"value": 12, "label": "12"}],
                    required=False,
                    condition='return fieldsData.api_source.value === "original"',
                    condition_python=lambda ports: ports["api_source"].value == "original",
                ),
                "resolution": InputPort(
                    name="resolution",
                    port_type=PortType.SELECT,
                    value="1280x720",
                    options=[{"value": "1280x720", "label": "1280x720 (16:9)"}, {"value": "720x1280", "label": "720x1280 (9:16)"}],
                    required=False,
                    condition='return fieldsData.api_source.value === "original"',
                    condition_python=lambda ports: ports["api_source"].value == "original",
                ),
                "model": InputPort(
                    name="model",
                    port_type=PortType.SELECT,
                    value="sora-2",
                    options=[{"value": "sora-2", "label": "sora-2"}, {"value": "sora-2-pro", "label": "sora-2-pro"}],
                    condition='return fieldsData.api_source.value === "original"',
                    condition_python=lambda ports: ports["api_source"].value == "original",
                ),
                "seed": InputPort(
                    name="seed",
                    port_type=PortType.NUMBER,
                    value=0,
                    required=False,
                    has_tooltip=True,
                    condition='return fieldsData.api_source.value === "original"',
                    condition_python=lambda ports: ports["api_source"].value == "original",
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="only_link",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )
