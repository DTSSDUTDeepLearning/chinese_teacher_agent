# MySQL 8.0.37 安装指南

本指南提供 Windows 操作系统下 MySQL Community Server 8.0.37 的详细安装步骤，可供自动化助手按步骤执行安装。

---

## 一、下载安装包

1. 打开浏览器，访问官方下载地址：
   - 地址：https://dev.mysql.com/downloads/installer/

2. 在页面中找到 "Windows (x86, 64-bit), MSI Installer" 选项。

3. 文件大小约 300-400 MB，点击 `Download` 按钮。

4. 页面跳转到登录提示时，点击下方的 `No thanks, just start my download.` 直接下载。

5. 等待下载完成，文件名为 `mysql-installer-community-8.0.37.0.msi`（版本号可能略有差异）。

---

## 二、运行安装程序

1. 打开文件下载目录（默认为 `Downloads` 文件夹）。

2. 找到下载的 MSI 安装文件，双击运行。

3. 如果系统提示 "Windows 已保护你的电脑"，点击 `更多信息`，然后点击 `仍要运行`。

4. 安装向导启动，进入 "License Agreement" 页面，勾选 `I accept the license terms`，点击 `Next`。

---

## 三、选择安装类型

1. 进入 "Choosing a Setup Type" 页面，显示多个安装选项：
   - `Developer Default`（开发者默认）
   - `Server only`（仅服务器）
   - `Client only`（仅客户端）
   - `Full`（完整安装）
   - `Custom`（自定义安装）

2. **关键步骤**：选择 `Server only`。

3. 选择理由：本项目仅需 MySQL 数据库服务运行，不需要 MySQL Workbench、Connector 等附加组件。

4. 点击 `Next` 按钮。

---

## 四、检查要求与执行安装

1. 进入 "Installation" 页面，显示将要安装的组件：`MySQL Server 8.0.37`。

2. 点击 `Execute` 按钮开始安装。

3. 等待安装进度完成，状态显示为 `Complete`。

4. 点击 `Next` 按钮进入配置阶段。

---

## 五、产品配置

1. 进入 "Product Configuration" 页面，点击 `Next` 开始配置 MySQL Server。

---

## 六、配置类型与网络

1. 进入 "Type and Networking" 页面：
   - Config Type：选择 `Development Computer`（开发计算机）
   - Connectivity：保持默认勾选 `TCP/IP`，Port 为 `3306`
   - X Protocol：保持默认勾选，Port 为 `33060`
   - Open Windows Firewall ports for network access：保持勾选

2. 点击 `Next` 按钮。

---

## 七、认证方法

1. 进入 "Authentication Method" 页面。

2. 选择 `Use Strong Password Encryption for Authentication (RECOMMENDED)`。

3. 点击 `Next` 按钮。

---

## 八、设置 root 密码

1. 进入 "Accounts and Roles" 页面。

2. 在 "MySQL Root Password" 区域输入 root 用户密码：
   - 输入密码（建议设置一个强密码，如包含大小写字母、数字和符号的组合）
   - 再次输入确认密码

3. **重要提示**：请牢记此密码，后续项目配置数据库连接时需要使用。

4. 点击 `Next` 按钮。

---

## 九、Windows 服务配置

1. 进入 "Windows Service" 页面：
   - Configure MySQL Server as a Windows Service：保持勾选
   - Windows Service Name：默认为 `MySQL80`，建议保持不变
   - Start the MySQL Server at System Startup：保持勾选
   - Run Windows Service as：选择 `Standard System Account`

2. 点击 `Next` 按钮。

---

## 十、应用配置

1. 进入 "Apply Configuration" 页面，点击 `Execute` 按钮应用所有配置。

2. 等待配置完成，所有步骤显示绿色对勾。

3. 点击 `Finish` 按钮。

4. 返回 "Product Configuration" 页面，点击 `Next`，然后点击 `Finish` 完成安装。

---

## 十一、验证安装

1. 按 `Win + R` 键打开运行对话框。

2. 输入 `cmd` 并按回车，打开命令提示符窗口。

3. 输入以下命令登录 MySQL（将 `your_password` 替换为安装时设置的 root 密码）：
   ```bash
   mysql -u root -p
   ```

4. 按回车后，系统提示输入密码，输入安装时设置的 root 密码（输入时密码不可见）。

5. 预期输出（显示 MySQL 版本信息及欢迎语）：
   ```
   Welcome to the MySQL monitor.  Commands end with ; or \g.
   Your MySQL connection id is 8
   Server version: 8.0.37 MySQL Community Server - GPL
   ...
   mysql>
   ```

6. 在 `mysql>` 提示符下输入以下命令查看数据库列表：
   ```sql
   SHOW DATABASES;
   ```

7. 预期输出包含默认数据库列表：
   ```
   +--------------------+
   | Database           |
   +--------------------+
   | information_schema |
   | mysql              |
   | performance_schema |
   | sys                |
   +--------------------+
   ```

8. 输入 `EXIT;` 退出 MySQL 命令行。

9. 如果以上步骤均正常执行，说明 MySQL 8.0.37 安装成功。

---

## 十二、常见问题

| 问题 | 解决方案 |
|------|----------|
| 命令行输入 `mysql` 提示找不到命令 | MySQL 的 bin 目录未加入系统 PATH。可手动将 `C:\Program Files\MySQL\MySQL Server 8.0\bin` 添加到系统环境变量 PATH 中，或使用完整路径调用。 |
| 登录时提示密码错误 | 确认输入的密码正确。如忘记密码，可通过 MySQL Installer 重新配置，或参考官方文档重置 root 密码。 |
| 端口 3306 被占用 | 检查是否有其他 MySQL 实例或应用占用了该端口。可在安装时修改端口，或关闭占用端口的程序。 |
| 安装过程中提示缺少 Visual C++ Redistributable | 根据提示下载并安装对应版本的 Microsoft Visual C++ Redistributable，然后重新运行 MySQL 安装程序。 |
