# Codex Personal

個人用のCodex skillと、それを支えるローカル自動化プロジェクトを管理する
リポジトリです。`~/.codex/skills` に直接cloneして使う前提です。

リポジトリ:

```text
https://github.com/Azkat/codex-personal.git
```

## 構成

```text
daily-report/            個人用Codex skill
_projects/               skillから使うローカル自動化・補助プロジェクト
_projects/daily-report/  デイリーレポート自動化
.system/                 Codex system skills。Git管理対象外
```

互換用のローカルシンボリックリンク:

```text
~/.codex/projects/daily-report -> ~/.codex/skills/_projects/daily-report
```

個人用skillは `~/.codex/skills` 配下の実ディレクトリとして置きます。
symlinkにしないことで、Codexが直接検出できます。

## Daily Report

運用手順や設定の詳細は `_projects/daily-report/app/README.md` にあります。

## 別のMacでのセットアップ

このリポジトリをCodexの個人用skillsディレクトリに直接cloneします。

```bash
mkdir -p ~/.codex ~/.codex/projects
git clone https://github.com/Azkat/codex-personal.git ~/.codex/skills
ln -s ~/.codex/skills/_projects/daily-report ~/.codex/projects/daily-report
```

シンボリックリンクとローカル仮想環境を作成します。

```bash
~/.codex/skills/_projects/daily-report/scripts/setup_device.sh
```

秘密情報とローカル設定はリポジトリ外に置きます。端末ごとに作り直します。

```text
~/.config/inoreader/
~/.config/raindrop/token.txt
~/.config/slack/webhooks
~/.config/youtube/
~/.config/openai/api_key.txt
```

## ローカル環境

依存関係が足りない場合は、仮想環境を作り直します。

```bash
~/.codex/skills/_projects/daily-report/scripts/setup_device.sh
```

秘密情報とローカル設定はリポジトリ外に置きます。

```text
~/.config/inoreader/
~/.config/raindrop/token.txt
~/.config/slack/webhooks
~/.config/youtube/
~/.config/openai/api_key.txt
```

## 実行

```bash
/usr/bin/python3 ~/.codex/projects/daily-report/app/daily_report.py
```

毎日のLaunchAgentをインストールします。

```bash
~/.codex/projects/daily-report/scripts/install_launch_agent.sh
```
