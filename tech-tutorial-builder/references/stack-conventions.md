# 各技术栈的项目目录惯例

实战项目（`project/`）遵循各语言/框架的社区惯例，让代码能真正运行。下面列出常见技术栈的结构与验证要点。新技术栈按同样精神类推。

## 通用要求

- 每个 project 必须有 `README.md`，含：项目简介、知识点对应表格、前置要求、安装运行步骤、目录结构说明、架构说明、可选的进阶练习。
- 知识点对应表格格式：

```markdown
| 知识点 | 在本项目中的体现 | 对应章节 |
|--------|------------------|----------|
| 装饰器 | @async_retry 自动重试 | 04 |
```

- 代码要真正可运行，串联多个知识点，避免玩具。

---

## 编译型语言

### Rust
```
project/
├── Cargo.toml          # 含 [dependencies]
├── README.md
└── src/
    └── main.rs         # 或 lib.rs + 多模块
```
依赖写进 Cargo.toml。如沙箱无 rustc 且网络受限装不了，做人工语法审校。

### Go
```
project/
├── go.mod
├── README.md
├── main.go             # Go 习惯相对扁平，包内文件平铺
├── checker.go
└── main_test.go        # 测试文件 _test.go 后缀
```
Go 项目惯例扁平，同一个包的文件放在同级。如无 go 工具链，人工审校。

---

## 脚本/解释型语言

### Python
```
project/
├── requirements.txt
├── README.md
├── <包名>/             # 用包目录组织
│   ├── __init__.py
│   ├── __main__.py     # 支持 python -m <包名> 运行
│   ├── core.py
│   └── ...
```
沙箱通常有 python3 + pip（用 `pip install --break-system-packages`）。**应实际运行示例和项目验证**。无网络装不了的第三方库，可写离线 mock 测试验证核心逻辑链路。

### TypeScript
```
project/
├── package.json
├── tsconfig.json       # strict: true，按需 experimentalDecorators
├── README.md
└── src/
    ├── client.ts
    ├── models.ts
    └── demo.ts         # 可运行的演示入口
```
沙箱有 node + tsc。**用 `npx tsc --strict` 实际编译，再 node 运行 demo 验证**。注意：Node 的 `Response` 构造器不接受 204 状态码（mock HTTP 时用 200）。

### Node.js
```
project/
├── package.json        # "type": "module" 用 ESM
├── .env.example
├── README.md
└── src/
    ├── app.js          # 入口
    ├── routes/         # 分层架构：路由
    ├── controllers/    # 控制器
    ├── services/       # 服务（业务逻辑+数据）
    └── middleware/     # 中间件
```
入口文件让"仅在直接运行时启动服务器"（`import.meta.url` 判断），便于测试导入。**应实际启动服务跑通 API 流程验证**（可写自包含测试脚本用内置 http 请求各端点）。

---

## 前端框架（需构建工具）

### Vue 3
```
project/
├── package.json        # vue + vue-router + pinia + vite + @vitejs/plugin-vue
├── vite.config.js
├── index.html          # Vite 入口
└── src/
    ├── main.js
    ├── router.js
    ├── App.vue
    ├── stores/         # Pinia store
    ├── composables/    # 组合式函数
    ├── views/          # 路由视图
    └── components/     # 组件
```
**验证**：装 `@vue/compiler-sfc` 单独编译每个 .vue（用 parse/compileScript/compileTemplate），再 `npx vite build` 实际构建整个项目（最强验证）。

### React
```
project/
├── package.json        # react + react-dom + react-router-dom + vite + @vitejs/plugin-react
├── vite.config.js
├── index.html
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── context/        # Context
    ├── hooks/          # 自定义 Hook
    ├── components/      # 组件
    └── views/          # 视图
```
**验证**：装 `@babel/core` + `@babel/preset-react` 编译每个 .jsx，再 `npx vite build` 实际构建。

---

## 配置/基础设施类

### Kubernetes
```
project/
├── README.md
├── k8s-manifests/      # 原始 YAML，按编号顺序
│   ├── 00-namespace.yaml
│   ├── 01-config-secret.yaml
│   └── ...
└── helm-chart/         # Helm Chart（参数化）
    ├── Chart.yaml
    ├── values.yaml
    ├── values-prod.yaml
    └── templates/      # 带 {{ }} 占位符
```
**验证**：用 Python `yaml.safe_load_all` 校验所有清单语法。helm 通常装不了（helm.sh 不在白名单），可写一个轻量 Python 渲染器模拟 `{{ .Values.x }}` 替换 + `{{- if }}` 条件块，验证渲染后是合法 YAML，并验证多环境 values 覆盖逻辑。

### Docker
```
project/
├── README.md
├── docker-compose.yml  # 编排多服务 + 网络 + 卷
├── .env.example
├── frontend/
│   ├── Dockerfile      # 可多阶段构建
│   ├── nginx.conf
│   └── ...
└── backend/
    ├── Dockerfile
    └── <源码>
```
**验证**：Docker daemon 在沙箱不可用，不做实际镜像构建。用 Python `yaml` 校验 docker-compose.yml 并断言编排逻辑（依赖顺序、卷挂载）；Dockerfile 人工审校（检查 FROM 等关键指令）；其中的应用源码用对应语言工具校验（如 `node --check`）；构建脚本可实际运行验证。

---

## 验证策略小结

| 类型 | 技术栈 | 验证方式 |
|------|--------|----------|
| 有运行时且沙箱支持 | Python, TypeScript, Node.js | 实际编译+运行 |
| 前端框架 | Vue, React | 编译器校验组件 + Vite 实际构建 |
| 缺工具链/网络受限 | Rust, Go | 人工语法审校 |
| 配置类 | K8s, Docker | 解析器校验语法 + 人工审校 + 可运行部分实测 |

报告时**如实说明**每个模块用了哪种验证、是否有环境限制导致无法实跑。
