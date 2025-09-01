# Simulink MCP 工具

一个基于 Model Context Protocol (MCP) 的 Simulink 自动化工具，允许用户通过自然语言输入自动创建和操作 Simulink Block Diagram。

## 功能特性

- 🤖 **自然语言接口**: 通过中文自然语言描述创建 Simulink 模型
- 🔧 **丰富的模块库**: 支持常用的 Simulink 模块（信号源、数学运算、传递函数等）
- 🔗 **智能连接**: 自动识别和连接模块端口
- ⚙️ **参数配置**: 自动设置模块的默认参数
- 🌐 **MCP 兼容**: 可与支持 MCP 的 AI 助手（如 Claude Desktop）集成

## 系统要求

- Python 3.8+
- MATLAB R2016b 或更高版本
- Simulink
- MATLAB Engine API for Python

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd Simulink_MCP
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 MATLAB Engine API for Python

**重要**: MATLAB Engine API 需要单独安装，不能通过 pip 直接安装。

#### macOS/Linux:
```bash
# 找到 MATLAB 安装目录
cd "/Applications/MATLAB_R2023b.app/extern/engines/python"  # 替换为你的 MATLAB 版本
python setup.py install
```

#### Windows:
```cmd
# 找到 MATLAB 安装目录
cd "C:\Program Files\MATLAB\R2023b\extern\engines\python"  # 替换为你的 MATLAB 版本
python setup.py install
```

**注意**: 
- 确保 Python 版本与 MATLAB 支持的版本兼容
- 在 M1/M2 Mac 上可能需要使用 Rosetta 模式运行 MATLAB

## 使用方法

### 1. 作为 MCP 服务器运行

#### 使用 MCP 开发工具:
```bash
# 启动开发服务器
mcp dev mcp_simulink_server.py

# 或使用 uv（如果已安装）
uv run mcp dev mcp_simulink_server.py
```

#### 直接运行:
```bash
python mcp_simulink_server.py
```

### 2. 在 Claude Desktop 中配置

编辑 Claude Desktop 的配置文件 `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "simulink": {
      "command": "python",
      "args": ["/path/to/Simulink_MCP/mcp_simulink_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/Simulink_MCP"
      }
    }
  }
}
```

### 3. 运行示例

```bash
python examples.py
```

## 可用工具

### 基础工具

- `start_matlab()`: 启动 MATLAB 引擎
- `new_model(name)`: 创建新的 Simulink 模型
- `add_block(model, lib_block, block_name, position)`: 添加模块
- `connect(model, src_block, src_port, dst_block, dst_port)`: 连接模块
- `set_block_param(model, block_name, params)`: 设置模块参数
- `save_model(model, path)`: 保存模型

### 智能工具

- `get_block_library()`: 获取可用模块库列表
- `smart_add_block(model, block_type, block_name, position, params)`: 智能添加模块
- `nl_build(command)`: 自然语言构建模型

## 支持的模块

### 信号源
- 正弦波 (Sine Wave)
- 阶跃 (Step)
- 斜坡 (Ramp)
- 常数 (Constant)
- 脉冲 (Pulse Generator)
- 随机 (Random Number)

### 数学运算
- 加法 (Add)
- 减法 (Subtract)
- 乘法 (Product)
- 除法 (Divide)
- 增益 (Gain)
- 积分 (Integrator)
- 微分 (Derivative)

### 传递函数
- 传递函数 (Transfer Function)
- 状态空间 (State-Space)
- PID 控制器 (PID Controller)

### 信号处理
- 示波器 (Scope)
- 显示 (Display)
- 输入/输出端口
- 开关 (Switch)
- 多路复用/解复用 (Mux/Demux)

### 逻辑运算
- 与门/或门/非门
- 比较器

## 自然语言示例

```python
# 基本示例
await nl_build("创建名为demo的模型，添加正弦波连接到示波器")

# 复杂示例
await nl_build("新建名为control的模型，添加阶跃信号，连接到PID控制器，再连接传递函数，最后连接示波器，然后保存")

# 数学运算
await nl_build("创建名为math的模型，添加两个常数，用加法器相加，结果显示在示波器上")
```

## 故障排除

### 常见问题

1. **MATLAB Engine 启动失败**
   - 确保 MATLAB 已正确安装
   - 检查 MATLAB Engine API 是否正确安装
   - 在 Mac M1/M2 上尝试使用 Rosetta 模式

2. **模块添加失败**
   - 确保 Simulink 许可证可用
   - 检查模块库路径是否正确
   - 验证模型名称是否有效

3. **连接失败**
   - 检查端口号是否正确（通常从 1 开始）
   - 确保源模块和目标模块都存在
   - 验证端口类型兼容性

### 调试模式

启用详细日志输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 开发计划

- [ ] 增强自然语言解析能力
- [ ] 支持更多 Simulink 模块
- [ ] 添加模型验证功能
- [ ] 支持子系统创建
- [ ] 集成仿真运行功能
- [ ] 添加模型可视化导出

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请创建 GitHub Issue。