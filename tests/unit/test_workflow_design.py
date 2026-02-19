from vectorvein.workflow.graph.workflow import Workflow
from vectorvein.workflow.nodes.file_processing import FileUpload
from vectorvein.workflow.nodes.llms import Deepseek
from vectorvein.workflow.nodes.text_processing import TemplateCompose
from vectorvein.workflow.nodes.tools import ProgrammingFunction
from vectorvein.workflow.nodes.output import Table, Text


def test_workflow_design():
    """Build a resume-screening workflow and verify its structure."""
    file_upload = FileUpload()
    pdf_parser = ProgrammingFunction()
    pdf_parser.add_port(name="upload_files", port_type="input", value=[], multiple=True, field_type="list", show=False)
    pdf_parser.ports["list_input"].value = False
    pdf_parser.ports["use_oversea_node"].value = False

    compose_prompt = TemplateCompose()
    compose_prompt.add_port(name="简历文本", port_type="textarea", show=False)
    compose_prompt.add_port(name="硬性要求", port_type="textarea", show=True, value="请输入硬性条件：")
    compose_prompt.ports["template"].value = "简历: {{简历文本}}\n要求: {{硬性要求}}"

    llm = Deepseek()
    llm.ports["llm_model"].value = "deepseek-reasoner"
    llm.ports["response_format"].value = "json_object"
    llm.ports["temperature"].value = 0.2

    filter_fn = ProgrammingFunction()
    filter_fn.add_port(name="json_list", port_type="input", multiple=True, field_type="list")
    filter_fn.ports["list_input"].value = False

    excel_fn = ProgrammingFunction()
    excel_fn.add_port(name="summary_list", port_type="input", multiple=True, field_type="list")
    excel_fn.ports["list_input"].value = False

    summary_table = Table()
    download_link = Text()
    download_link.ports["output_title"].value = "下载筛选后简历Excel"

    workflow = Workflow()
    workflow.add_nodes([file_upload, pdf_parser, compose_prompt, llm, filter_fn, excel_fn, summary_table, download_link])

    workflow.connect(file_upload, "output", pdf_parser, "upload_files")
    workflow.connect(pdf_parser, "output", compose_prompt, "简历文本")
    workflow.connect(compose_prompt, "output", llm, "prompt")
    workflow.connect(llm, "output", filter_fn, "json_list")
    workflow.connect(filter_fn, "output", summary_table, "content")
    workflow.connect(filter_fn, "output", excel_fn, "summary_list")
    workflow.connect(excel_fn, "output", download_link, "text")

    check_result = workflow.check()
    assert check_result["no_cycle"], "Workflow should have no cycles"
    assert check_result["no_isolated_nodes"], "Workflow should have no isolated nodes"

    workflow.layout()
    data = workflow.to_dict()

    assert len(data["nodes"]) == 8
    assert len(data["edges"]) == 7
