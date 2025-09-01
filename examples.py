#!/usr/bin/env python3
"""
Simulink MCP工具使用示例

这个文件展示了如何使用Simulink MCP工具通过自然语言创建Block Diagram。
注意：运行这些示例需要先安装MATLAB Engine API for Python。
"""

import asyncio
from mcp_simulink_server import (
    start_matlab, new_model, smart_add_block, connect, 
    set_block_param, save_model, nl_build, get_block_library
)


async def example_basic_sine_scope():
    """示例1: 创建基本的正弦波-示波器模型"""
    print("=== 示例1: 基本正弦波-示波器模型 ===")
    
    # 启动MATLAB引擎
    result = await start_matlab()
    print(result)
    
    # 创建新模型
    result = await new_model("sine_scope_demo")
    print(result)
    
    # 添加正弦波源
    result = await smart_add_block(
        "sine_scope_demo", "正弦波", "SineWave1", 
        [50, 50, 120, 80], {"Amplitude": "2", "Frequency": "0.5"}
    )
    print(result)
    
    # 添加示波器
    result = await smart_add_block(
        "sine_scope_demo", "示波器", "Scope1", [250, 45, 300, 85]
    )
    print(result)
    
    # 连接模块
    result = await connect("sine_scope_demo", "SineWave1", 1, "Scope1", 1)
    print(result)
    
    # 保存模型
    result = await save_model("sine_scope_demo")
    print(result)
    print()


async def example_pid_control():
    """示例2: 创建PID控制系统"""
    print("=== 示例2: PID控制系统 ===")
    
    # 创建新模型
    result = await new_model("pid_control_demo")
    print(result)
    
    # 添加阶跃输入
    result = await smart_add_block(
        "pid_control_demo", "阶跃", "StepInput", 
        [50, 50, 100, 80], {"Time": "1", "After": "1"}
    )
    print(result)
    
    # 添加PID控制器
    result = await smart_add_block(
        "pid_control_demo", "PID", "PIDController", 
        [150, 45, 200, 85], {"P": "2", "I": "0.5", "D": "0.1"}
    )
    print(result)
    
    # 添加被控对象（传递函数）
    result = await smart_add_block(
        "pid_control_demo", "传递函数", "Plant", 
        [250, 45, 300, 85]
    )
    print(result)
    
    # 添加示波器
    result = await smart_add_block(
        "pid_control_demo", "示波器", "OutputScope", [350, 45, 400, 85]
    )
    print(result)
    
    # 连接模块
    await connect("pid_control_demo", "StepInput", 1, "PIDController", 1)
    await connect("pid_control_demo", "PIDController", 1, "Plant", 1)
    await connect("pid_control_demo", "Plant", 1, "OutputScope", 1)
    
    # 保存模型
    result = await save_model("pid_control_demo")
    print(result)
    print()


async def example_natural_language():
    """示例3: 使用自然语言创建模型"""
    print("=== 示例3: 自然语言创建模型 ===")
    
    # 示例命令1: 简单的正弦波-示波器
    command1 = "创建名为nl_demo1的模型，添加正弦波连接到示波器，然后保存"
    print(f"命令: {command1}")
    result = await nl_build(command1)
    print(result)
    print()
    
    # 示例命令2: 更复杂的系统
    command2 = "新建名为nl_demo2的模型，添加阶跃信号，连接到增益模块，再连接积分器，最后连接示波器"
    print(f"命令: {command2}")
    result = await nl_build(command2)
    print(result)
    print()
    
    # 示例命令3: 数学运算
    command3 = "创建名为math_demo的模型，添加两个常数，用加法器相加，结果显示在示波器上"
    print(f"命令: {command3}")
    result = await nl_build(command3)
    print(result)
    print()


async def example_block_library():
    """示例4: 查看可用模块库"""
    print("=== 示例4: 可用模块库 ===")
    result = await get_block_library()
    print(result)


async def main():
    """运行所有示例"""
    print("Simulink MCP工具使用示例\n")
    print("注意：这些示例需要MATLAB和Simulink已安装并配置好MATLAB Engine API for Python\n")
    
    try:
        # 运行示例
        await example_block_library()
        await example_basic_sine_scope()
        await example_pid_control()
        await example_natural_language()
        
        print("所有示例运行完成！")
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确安装MATLAB Engine API for Python")


if __name__ == "__main__":
    asyncio.run(main())