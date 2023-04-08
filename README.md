# EhFavDownloader

[English](README-EN.md)

一个备份 E-Hentai 收藏夹的脚本。文件格式适配 EhViewer，自动生成 .ehviewer 文件，方便恢复下载项。

## 贴心提示

如果你有什么不会的地方（例如如何获取 Cookies），请优先请教谷歌、必应等搜索引擎或诸如 ChatGPT 等人工智能。

这些产品聚集了人类智慧的结晶，问他们比到处喊大佬效率要高的多。

## 免责声明

本脚本是个人自用脚本，托管在 GitHub 上只是为了方便网友需求。由于个人水平有限，代码必定含有大量问题。你应当有一定的动手能力再使用本脚本。

你应当清楚并知晓，本脚本不为潜在可能造成的任何损失而负责，包括但不限于 IP 被封锁、账号被封禁、文件丢失等等潜在的风险。详情请查看本项目所使用的 [许可证](LICENSE)。

## 关于 e-hentai.org 站点的下载提示

由于 e-hentai.org 最近部署了 CloudFlare 盾，本脚本并未使用无头浏览器执行 JS 脚本，暂时无法绕过。由于 CloudFlare 盾的触发概率变高，通过 e-hentai.org 站点下载很可能会触发 403 拒绝访问。暂时的解决方法是使用 exhentai.org 站点进行下载，请自行斟酌是否使用 e-hentai.org 进行下载。

## 使用方法

- 安装一份 [Python](https://www.python.org)。按理来说最低版本需求为 3.7，但本脚本是在 3.11 版本写成的，所以建议使用 3.11 版本。
- 安装本项目所需要的依赖。一般来说，你只需执行
  ```shell
  pip install -r requirements.txt
  ```
  即可。
- 复制一份 config.yaml.example，将其重命名为 config.yaml，之后根据文件中的注释对相应的配置进行修改。需要注意的是 YAML 的语法，如果你不清楚可以请教搜索引擎。
- 运行脚本或者是将脚本加入相关的计划任务（如 Windows 任务计划程序、Linux Crontab 等）即可。
