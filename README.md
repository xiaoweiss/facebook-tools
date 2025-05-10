# Facebook 自动化工具

一个用于自动化 Facebook 广告账户操作的工具，支持自动查询余额和创建广告活动。

## 功能特点

- 支持 Facebook 广告账户自动化操作
- 提供图形用户界面
- 支持定时任务
- 支持 Windows 和 macOS 平台

## 构建指南

### 本地构建

1. 安装依赖:

```
pip install -r requirements.txt
```

2. 构建应用程序:

macOS:

```
python build_macos.py
```

Windows:

```
python build.py
```

### GitHub Actions 构建

本项目支持通过 GitHub Actions 自动构建，只需推送到 main 或 master 分支，或者手动触发工作流即可。

## 使用方法

1. 运行构建好的 FbAutoTool 应用程序
2. 输入授权账号进行验证
3. 选择要执行的任务类型
4. 根据需要配置定时设置
5. 点击"开始执行"按钮

## 环境要求

- Python 3.9+
- 已安装 AdsPower 浏览器
- 网络可访问 Facebook

## 常见问题

如果遇到构建问题，请确保:

1. 所有依赖已正确安装
2. 系统中有 PyInstaller 的正确版本(6.3.0)
3. 所有文件路径正确无误

如构建后运行失败，可以尝试:

1. 检查是否有缺失的配置文件
2. 确保 app_config.json 文件存在
3. 检查是否有权限问题
