from vectorvein.workflow.nodes.llms import Gemini


def test_gemini_sampling_defaults_are_optional():
    node = Gemini()
    for name in ("temperature", "top_p"):
        port = node.ports[name]
        assert port.value is None
        assert port.required is False
        port.value = 0.5
        assert port.value == 0.5
