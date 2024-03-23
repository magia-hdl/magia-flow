from tempfile import TemporaryDirectory

import pytest

from magia_flow.formal import SbyTask, sby_installed


@pytest.mark.skipif(not sby_installed(), reason="SymbiYosys not installed")
def test_sby_task_success():
    code = """
    module oscillator (
        input  logic   clk,
        input  logic   reset,
        output logic   pulse
    );
    logic pulse_cur; assign pulse = pulse_cur;
    always_ff@(posedge clk)begin
        if (reset)
            pulse_cur <= 0;
        else
            pulse_cur <= ~pulse_cur;
    end

    `ifdef FORMAL
    logic reset_0 = 0;    logic reset_n_0 = 0;    logic pulse_0 = 0;
    always@(posedge clk)begin
        reset_0 <= reset; reset_n_0 <= ~reset; pulse_0 <= pulse;
    end

    always@(posedge clk)begin
        a_reset:  assert({reset_0 , !pulse} != 2'b10);
        a_osc:    assert({reset_n_0 , pulse != pulse_0} !== 2'b10);
    end
    `endif
    endmodule
    """
    with TemporaryDirectory(suffix="magia-sby-") as workdir:
        task = SbyTask.from_code("oscillator", code, work_dir=workdir)
        task.run()
        assert task.result.passed
        test_passed = {
            tc["id"] for tc in task.result.tests
        }
        assert "a_reset" in test_passed
        assert "a_osc" in test_passed


@pytest.mark.skipif(not sby_installed(), reason="SymbiYosys not installed")
def test_sby_task_assertion_failure():
    code = """
    module oscillator (
        input  logic   clk,
        input  logic   reset,
        output logic   pulse
    );
    logic pulse_cur; assign pulse = pulse_cur;
    always_ff@(posedge clk)begin
        if (reset)
            pulse_cur <= 0;
        else
            pulse_cur <=  pulse_cur;  // BUG HERE
    end

    `ifdef FORMAL
    logic reset_0 = 0;    logic reset_n_0 = 0;    logic pulse_0 = 0;
    always@(posedge clk)begin
        reset_0 <= reset; reset_n_0 <= ~reset; pulse_0 <= pulse;
    end

    always@(posedge clk)begin
        a_reset:  assert({reset_0 , !pulse} != 2'b10);

        // This assertion will fail
        a_osc:    assert({reset_n_0 , pulse != pulse_0} !== 2'b10);
    end
    `endif
    endmodule
    """
    with TemporaryDirectory(suffix="magia-sby-") as workdir:
        task = SbyTask.from_code("oscillator", code, work_dir=workdir)
        task.run()
        assert not task.result.passed
        for tc in task.result.tests:
            if tc["id"] == "a_osc":
                assert tc["status"] == "failed"
