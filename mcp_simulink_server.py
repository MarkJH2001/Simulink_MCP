import asyncio
import logging
import os
import glob
from typing import Optional, Dict, Any, List

from mcp.server.fastmcp import FastMCP

try:
    # MATLAB Engine is optional at import time; we lazily initialize when first used
    import matlab.engine  # type: ignore
except Exception:  # pragma: no cover
    matlab = None  # type: ignore
    matlab_engine_available = False
else:
    matlab_engine_available = True


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimulinkMCP")


class MatlabSimulinkController:
    """Wrap MATLAB Engine API for Simulink operations."""

    def __init__(self) -> None:
        self.eng: Optional[Any] = None

    async def start(self) -> None:
        if self.eng is not None:
            return
        loop = asyncio.get_event_loop()
        logger.info("Starting MATLAB engine...")
        # Start engine in a separate thread to avoid blocking event loop
        self.eng = await loop.run_in_executor(None, matlab.engine.start_matlab)  # type: ignore
        logger.info("MATLAB engine started")

    async def stop(self) -> None:
        if self.eng is None:
            return
        logger.info("Stopping MATLAB engine...")
        await asyncio.get_event_loop().run_in_executor(None, self.eng.quit)
        self.eng = None
        logger.info("MATLAB engine stopped")

    def _ensure(self) -> None:
        if self.eng is None:
            raise RuntimeError("MATLAB engine not started. Call start_matlab first.")

    async def new_model(self, name: str) -> str:
        self._ensure()
        eng = self.eng
        assert eng is not None
        def _new_model() -> str:
            try:
                eng.eval("bdclose('all')", nargout=0)
            except Exception:
                pass
            eng.eval(f"new_system('{name}')", nargout=0)
            eng.eval(f"open_system('{name}')", nargout=0)
            return name
        return await asyncio.get_event_loop().run_in_executor(None, _new_model)

    async def add_block(self, model: str, lib_block: str, block_name: str, position: Optional[List[int]] = None) -> str:
        self._ensure()
        eng = self.eng
        assert eng is not None
        pos = position or [30, 30, 90, 90]
        pos_str = f"[{pos[0]} {pos[1]} {pos[2]} {pos[3]}]"
        full_path = f"{model}/{block_name}"
        def _add_block() -> str:
            eng.eval(f"add_block('{lib_block}','{full_path}','Position','{pos_str}')", nargout=0)
            return full_path
        return await asyncio.get_event_loop().run_in_executor(None, _add_block)

    async def connect(self, model: str, src_block: str, src_port: int, dst_block: str, dst_port: int) -> str:
        self._ensure()
        eng = self.eng
        assert eng is not None
        def _connect() -> str:
            src = f"{src_block}/{src_port}"
            dst = f"{dst_block}/{dst_port}"
            eng.eval(f"add_line('{model}','{src}','{dst}','autorouting','on')", nargout=0)
            return f"{src} -> {dst}"
        return await asyncio.get_event_loop().run_in_executor(None, _connect)

    async def set_param(self, block_path: str, params: Dict[str, Any]) -> None:
        self._ensure()
        eng = self.eng
        assert eng is not None
        def _set() -> None:
            for k, v in params.items():
                eng.set_param(block_path, k, str(v), nargout=0)
        await asyncio.get_event_loop().run_in_executor(None, _set)

    async def save_model(self, model: str, path: Optional[str] = None) -> str:
        self._ensure()
        eng = self.eng
        assert eng is not None
        def _save() -> str:
            if path:
                eng.save_system(model, path, nargout=0)
                return path
            else:
                # 设置默认保存路径为桌面
                desktop_path = os.path.expanduser("~/Desktop")
                default_path = os.path.join(desktop_path, f"{model}.slx")
                eng.save_system(model, default_path, nargout=0)
                return default_path
        return await asyncio.get_event_loop().run_in_executor(None, _save)

    async def delete_block(self, model: str, block_name: str) -> str:
        """删除模型中的模块"""
        self._ensure()
        eng = self.eng
        assert eng is not None
        full_path = f"{model}/{block_name}"
        
        def _delete_block() -> str:
            try:
                # 删除模块
                eng.eval(f"delete_block('{full_path}')", nargout=0)
                return f"已删除模块: {full_path}"
            except Exception as e:
                return f"删除模块失败: {str(e)}"
        
        return await asyncio.get_event_loop().run_in_executor(None, _delete_block)

    async def open_model(self, file_path: str) -> str:
        """打开本地Simulink模型文件"""
        self._ensure()
        eng = self.eng
        assert eng is not None
        def _open_model() -> str:
            try:
                # 使用open_system命令打开模型文件，不期望返回值
                eng.open_system(file_path, nargout=0)
                # 从文件路径提取模型名（不含扩展名）
                model_name = os.path.splitext(os.path.basename(file_path))[0]
                return f"已打开模型: {model_name} (来自文件: {file_path})"
            except Exception as e:
                return f"打开模型失败: {str(e)}"
        return await asyncio.get_event_loop().run_in_executor(None, _open_model)

    async def arrange_system(self, model: str) -> str:
        """自动排列系统布局"""
        self._ensure()
        eng = self.eng
        assert eng is not None
        def _arrange() -> str:
            try:
                # 使用Simulink官方的arrangeSystem命令自动排列布局
                eng.eval(f"Simulink.BlockDiagram.arrangeSystem('{model}')", nargout=0)
                return f"已自动排列模型布局: {model}"
            except Exception as e:
                return f"自动排列失败: {str(e)}"
        return await asyncio.get_event_loop().run_in_executor(None, _arrange)


mcp = FastMCP("Simulink-MCP")


@mcp.tool()
async def start_matlab() -> str:
    """启动MATLAB引擎（若未启动）"""
    if not matlab_engine_available:
        return "MATLAB Engine for Python 未安装或不可用。请先安装。"
    await ctrl.start()
    return "MATLAB Engine 已启动"


@mcp.tool()
async def new_model(name: str) -> str:
    """新建Simulink模型"""
    await ctrl.start()
    model = await ctrl.new_model(name)
    return f"模型已创建: {model}"


@mcp.tool()
async def add_block(model: str, lib_block: str, block_name: str, position: Optional[List[int]] = None) -> str:
    """添加模块到模型中

    Args:
        model: 模型名称，例如 'mymodel'
        lib_block: 库模块路径，例如 'simulink/Sources/Sine Wave'
        block_name: 在模型中的模块名，例如 'Sine1'
        position: 可选位置 [left top right bottom]
    """
    await ctrl.start()
    full = await ctrl.add_block(model, lib_block, block_name, position)
    return f"已添加模块: {full}"


@mcp.tool()
async def connect(model: str, src_block: str, src_port: int, dst_block: str, dst_port: int, auto_arrange: bool = True) -> str:
    """连接两个模块端口，可选择是否自动排列布局"""
    await ctrl.start()
    line = await ctrl.connect(model, src_block, src_port, dst_block, dst_port)
    result_msg = f"已连接: {line}"
    
    # 自动排列布局
    if auto_arrange:
        arrange_result = await ctrl.arrange_system(model)
        result_msg += f"\n{arrange_result}"
    
    return result_msg


@mcp.tool()
async def set_block_param(model: str, block_name: str, params: Dict[str, Any], auto_arrange: bool = True) -> str:
    """为模块设置参数，可选择是否自动排列布局
    
    Args:
        model: 模型名称，例如 'mymodel'
        block_name: 模块名，例如 'Gain1'
        params: 参数字典，例如 {'Gain': '2', 'SaturateOnIntegerOverflow': 'off'}
        auto_arrange: 是否在设置参数后自动排列布局，默认为True
    """
    await ctrl.start()
    block_path = f"{model}/{block_name}"
    await ctrl.set_param(block_path, params)
    
    param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
    result_msg = f"参数已更新: {block_path} ({param_str})"
    
    # 自动排列布局
    if auto_arrange:
        arrange_result = await ctrl.arrange_system(model)
        result_msg += f"\n{arrange_result}"
    
    return result_msg


@mcp.tool()
async def save_model(model: str, path: Optional[str] = None) -> str:
    """保存模型到文件"""
    await ctrl.start()
    saved = await ctrl.save_model(model, path)
    return f"模型已保存: {saved}"


@mcp.tool()
async def delete_block(model: str, block_name: str, auto_arrange: bool = True) -> str:
    """删除模型中的模块，可选择是否自动排列布局
    
    Args:
        model: 模型名称，例如 'mymodel'
        block_name: 要删除的模块名，例如 'Sine1'
        auto_arrange: 是否在删除后自动排列布局，默认为True
    """
    await ctrl.start()
    result = await ctrl.delete_block(model, block_name)
    
    # 检查删除是否成功
    if "已删除模块" in result and auto_arrange:
        arrange_result = await ctrl.arrange_system(model)
        result += f"\n{arrange_result}"
    
    return result


@mcp.tool()
async def find_simulink_models(search_path: str = "~/Desktop", pattern: str = "*.slx", recursive: bool = False) -> str:
    """查找本地Simulink模型文件
    
    Args:
        search_path: 搜索路径，默认为桌面
        pattern: 文件模式，默认为 '*.slx'，也支持 '*.mdl'
        recursive: 是否递归搜索子目录，默认为False（仅搜索当前目录）
    """
    # 展开用户路径
    expanded_path = os.path.expanduser(search_path)
    
    # 检查路径是否存在
    if not os.path.exists(expanded_path):
        return f"搜索路径不存在: {expanded_path}"
    
    # 支持多种Simulink文件格式
    patterns = []
    if pattern == "*.slx":
        patterns = ["*.slx", "*.mdl"]
    elif pattern == "*.mdl":
        patterns = ["*.mdl", "*.slx"]
    else:
        patterns = [pattern]
    
    found_files = []
    for pat in patterns:
        if recursive:
            # 递归搜索子目录
            search_pattern = os.path.join(expanded_path, "**", pat)
            files = glob.glob(search_pattern, recursive=True)
        else:
            # 仅搜索当前目录
            search_pattern = os.path.join(expanded_path, pat)
            files = glob.glob(search_pattern, recursive=False)
        found_files.extend(files)
    
    # 去重并排序
    found_files = sorted(list(set(found_files)))
    
    if not found_files:
        search_scope = "及子目录" if recursive else ""
        return f"在 {expanded_path}{search_scope} 中未找到Simulink模型文件 ({', '.join(patterns)})"
    
    search_scope = "（包含子目录）" if recursive else "（仅当前目录）"
    result = f"在 {expanded_path} 中找到 {len(found_files)} 个Simulink模型文件{search_scope}:\n\n"
    
    for i, file_path in enumerate(found_files, 1):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        # 显示相对于搜索路径的目录信息
        relative_dir = os.path.dirname(os.path.relpath(file_path, expanded_path))
        if relative_dir and relative_dir != ".":
            result += f"{i}. {file_name} ({file_size_mb:.2f} MB) [在子目录: {relative_dir}]\n"
        else:
            result += f"{i}. {file_name} ({file_size_mb:.2f} MB)\n"
        result += f"   路径: {file_path}\n\n"
    
    return result


@mcp.tool()
async def open_model(file_path: str, auto_arrange: bool = True) -> str:
    """打开本地Simulink模型文件
    
    Args:
        file_path: 模型文件的绝对路径或相对路径
        auto_arrange: 是否在打开后自动排列布局，默认为True
    """
    await ctrl.start()
    
    # 展开用户路径
    expanded_path = os.path.expanduser(file_path)
    
    # 检查文件是否存在
    if not os.path.exists(expanded_path):
        return f"文件不存在: {expanded_path}"
    
    # 检查文件扩展名
    _, ext = os.path.splitext(expanded_path)
    if ext.lower() not in ['.slx', '.mdl']:
        return f"不支持的文件格式: {ext}。支持的格式: .slx, .mdl"
    
    # 打开模型
    result = await ctrl.open_model(expanded_path)
    
    # 如果成功打开且需要自动排列，则进行布局优化
    if "已打开模型" in result and auto_arrange:
        # 从结果中提取模型名
        try:
            model_name = result.split("已打开模型: ")[1].split(" (来自文件:")[0]
            arrange_result = await ctrl.arrange_system(model_name)
            result += f"\n{arrange_result}"
        except Exception as e:
            result += f"\n自动排列失败: {str(e)}"
    
    return result


@mcp.tool()
async def arrange_system(model: str) -> str:
    """自动排列系统布局 - 使用Simulink官方的arrangeSystem命令优化模块布局"""
    await ctrl.start()
    result = await ctrl.arrange_system(model)
    return result


# Simulink常用模块库映射
BLOCK_LIBRARY = {
    # 信号源
    "正弦波": "simulink/Sources/Sine Wave",
    "sine": "simulink/Sources/Sine Wave",
    "阶跃": "simulink/Sources/Step",
    "step": "simulink/Sources/Step",
    "斜坡": "simulink/Sources/Ramp",
    "ramp": "simulink/Sources/Ramp",
    "常数": "simulink/Sources/Constant",
    "constant": "simulink/Sources/Constant",
    "脉冲": "simulink/Sources/Pulse Generator",
    "pulse": "simulink/Sources/Pulse Generator",
    "随机": "simulink/Sources/Random Number",
    "random": "simulink/Sources/Random Number",
    
    # 数学运算
    "加法": "simulink/Math Operations/Add",
    "add": "simulink/Math Operations/Add",
    "减法": "simulink/Math Operations/Subtract",
    "subtract": "simulink/Math Operations/Subtract",
    "乘法": "simulink/Math Operations/Product",
    "multiply": "simulink/Math Operations/Product",
    "除法": "simulink/Math Operations/Divide",
    "divide": "simulink/Math Operations/Divide",
    "增益": "simulink/Math Operations/Gain",
    "gain": "simulink/Math Operations/Gain",
    "积分": "simulink/Continuous/Integrator",
    "integrator": "simulink/Continuous/Integrator",
    "微分": "simulink/Continuous/Derivative",
    "derivative": "simulink/Continuous/Derivative",
    
    # 传递函数
    "传递函数": "simulink/Continuous/Transfer Fcn",
    "transfer": "simulink/Continuous/Transfer Fcn",
    "状态空间": "simulink/Continuous/State-Space",
    "statespace": "simulink/Continuous/State-Space",
    "pid": "simulink/Continuous/PID Controller",
    "PID": "simulink/Continuous/PID Controller",
    
    # 信号处理
    "示波器": "simulink/Sinks/Scope",
    "scope": "simulink/Sinks/Scope",
    "显示": "simulink/Sinks/Display",
    "display": "simulink/Sinks/Display",
    "输出": "simulink/Sinks/Out1",
    "output": "simulink/Sinks/Out1",
    "输入": "simulink/Sources/In1",
    "input": "simulink/Sources/In1",
    "开关": "simulink/Signal Routing/Switch",
    "switch": "simulink/Signal Routing/Switch",
    "多路复用": "simulink/Signal Routing/Mux",
    "mux": "simulink/Signal Routing/Mux",
    "解复用": "simulink/Signal Routing/Demux",
    "demux": "simulink/Signal Routing/Demux",
    
    # 逻辑运算
    "与门": "simulink/Logic and Bit Operations/Logical Operator",
    "and": "simulink/Logic and Bit Operations/Logical Operator",
    "或门": "simulink/Logic and Bit Operations/Logical Operator",
    "or": "simulink/Logic and Bit Operations/Logical Operator",
    "非门": "simulink/Logic and Bit Operations/Logical Operator",
    "not": "simulink/Logic and Bit Operations/Logical Operator",
    "比较": "simulink/Logic and Bit Operations/Relational Operator",
    "compare": "simulink/Logic and Bit Operations/Relational Operator",
}

# 默认参数配置
DEFAULT_PARAMS = {
    "simulink/Sources/Sine Wave": {"Amplitude": "1", "Frequency": "1"},
    "simulink/Sources/Step": {"Time": "1", "Before": "0", "After": "1"},
    "simulink/Sources/Constant": {"Value": "1"},
    "simulink/Math Operations/Gain": {"Gain": "1"},
    "simulink/Continuous/PID Controller": {"P": "1", "I": "1", "D": "0"},
}

@mcp.tool()
async def get_block_library() -> str:
    """获取可用的Simulink模块库"""
    result = "可用的Simulink模块:\n\n"
    categories = {
        "信号源": ["正弦波", "阶跃", "斜坡", "常数", "脉冲", "随机"],
        "数学运算": ["加法", "减法", "乘法", "除法", "增益", "积分", "微分"],
        "传递函数": ["传递函数", "状态空间", "PID"],
        "信号处理": ["示波器", "显示", "输出", "输入", "开关", "多路复用", "解复用"],
        "逻辑运算": ["与门", "或门", "非门", "比较"]
    }
    
    for category, blocks in categories.items():
        result += f"**{category}:**\n"
        for block in blocks:
            lib_path = BLOCK_LIBRARY.get(block, "未知")
            result += f"  - {block} ({lib_path})\n"
        result += "\n"
    
    return result

@mcp.tool()
async def smart_add_block(model: str, block_type: str, block_name: str, position: Optional[List[int]] = None, params: Optional[Dict[str, Any]] = None, auto_arrange: bool = True) -> str:
    """智能添加模块，自动设置默认参数，可选择是否自动排列布局"""
    await ctrl.start()
    
    # 查找模块库路径
    lib_block = BLOCK_LIBRARY.get(block_type.lower())
    if not lib_block:
        return f"未找到模块类型: {block_type}。请使用 get_block_library 查看可用模块。"
    
    # 添加模块
    full_path = await ctrl.add_block(model, lib_block, block_name, position)
    
    # 设置默认参数
    default_params = DEFAULT_PARAMS.get(lib_block, {})
    if params:
        default_params.update(params)
    
    result_msg = ""
    if default_params:
        await ctrl.set_param(full_path, default_params)
        param_str = ", ".join([f"{k}={v}" for k, v in default_params.items()])
        result_msg = f"已添加模块: {full_path}，参数: {param_str}"
    else:
        result_msg = f"已添加模块: {full_path}"
    
    # 自动排列布局
    if auto_arrange:
        arrange_result = await ctrl.arrange_system(model)
        result_msg += f"\n{arrange_result}"
    
    return result_msg


ctrl = MatlabSimulinkController()

if __name__ == "__main__":
    # 开发模式：允许作为独立MCP服务器运行（stdio）
    # 例如：uv run mcp dev mcp_server.py 或 python mcp_server.py stdio
    # 添加调试日志
    logger.info("Starting Simulink MCP Server...")
    logger.info("Available tools: start_matlab, new_model, open_model, add_block, delete_block, connect, set_block_param, save_model, arrange_system, find_simulink_models, get_block_library, smart_add_block")
    
    # 运行MCP服务器
    mcp.run()