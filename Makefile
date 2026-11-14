# 人もエージェントもCIも、確認はこの1本を通す
.PHONY: setup check format lint types layers test docs-push docs-verify

# uv のキャッシュを作業フォルダの中に置く。エージェントのサンドボックスの中からも同じコマンドが動く
export UV_CACHE_DIR ?= .uv-cache

setup:
	uv sync

check: lint types layers test

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .

types:
	uv run mypy

layers:
	uv run python tools/check_layers.py

test:
	uv run pytest

# 仕様を Confluence へ書き込む、一致を確かめる（接続先は環境変数で渡す）
docs-push:
	uv run python tools/docs_sync.py push

docs-verify:
	uv run python tools/docs_sync.py verify
