import click
import sys

from core.utils import setup_logging
from core.browser import BrowserDriver, DouyinMusicConsole
from core.creator import (
    generate_lyrics,
    save_lyrics,
    build_full_workflow,
    build_prompt,
)


@click.group()
@click.option("--headless", is_flag=True, default=False, help="无头模式运行浏览器")
@click.option("-v", "--verbose", is_flag=True, default=False, help="调试日志")
@click.pass_context
def cli(ctx: click.Context, headless: bool, verbose: bool):
    """抖音音乐控制台自动化 CLI"""
    setup_logging(level=10 if verbose else 20)
    ctx.ensure_object(dict)
    ctx.obj["headless"] = headless


@cli.command()
@click.option("--keep-open", is_flag=True, default=False, help="不自动关闭浏览器")
@click.pass_context
def open_console(ctx: click.Context, keep_open: bool):
    """打开抖音音乐控制台，等待扫码登录。"""
    bd = BrowserDriver(headless=ctx.obj["headless"])
    try:
        driver = bd.start()
        console = DouyinMusicConsole(driver)
        console.open()
        ok = console.require_login()
        click.echo(f"登录状态: {'成功' if ok else '失败/超时'}")
        if keep_open:
            click.prompt("按回车键关闭浏览器", default=True)
    finally:
        if not keep_open:
            bd.quit()


@cli.command()
@click.option("-t", "--theme", default="励志", help="歌词主题 (抒情/励志/爱情/古风)")
@click.option("-m", "--mood", default="轻快", help="情绪")
@click.option("-l", "--lines", default=8, type=int, help="歌词行数")
@click.option("-o", "--out", default=None, help="保存文件名")
def lyrics(theme: str, mood: str, lines: int, out: str):
    """本地生成歌词，保存到 outputs 目录。"""
    text = generate_lyrics(theme=theme, lines=lines)
    path = save_lyrics(text, filename=out)
    click.echo(f"[歌词]\n{text}\n")
    click.echo(f"已保存: {path}")


@cli.command()
@click.option("-t", "--theme", default="励志")
@click.option("-m", "--mood", default="轻快")
@click.option("-l", "--lines", default=8, type=int)
def create(theme: str, mood: str, lines: int):
    """本地生成完整作品素材 (歌词 + 音乐占位)。"""
    result = build_full_workflow(theme=theme, mood=mood, lines=lines)
    click.echo(f"标题: {result['title']}")
    click.echo(f"Prompt: {result['prompt']}")
    click.echo(f"歌词文件: {result['lyrics_path']}")
    click.echo(f"音乐文件: {result['music_path']}")


@cli.command()
@click.argument("file_path")
@click.option("-t", "--title", default=None, help="作品标题")
@click.pass_context
def upload(ctx: click.Context, file_path: str, title: str):
    """上传本地音乐文件到抖音音乐控制台。"""
    bd = BrowserDriver(headless=ctx.obj["headless"])
    try:
        driver = bd.start()
        console = DouyinMusicConsole(driver)
        console.open()
        if not console.require_login():
            click.echo("登录失败，退出", err=True)
            sys.exit(1)
        console.goto_section("上传") or console.goto_section("创作音乐")
        ok = console.upload_music(file_path, title=title)
        click.echo(f"上传结果: {'成功' if ok else '失败'}")
        click.prompt("按回车键关闭浏览器", default=True)
    finally:
        bd.quit()


@cli.command()
@click.option("-t", "--theme", default="励志")
@click.option("-m", "--mood", default="轻快")
@click.option("-l", "--lines", default=8, type=int)
@click.pass_context
def auto_workflow(ctx: click.Context, theme: str, mood: str, lines: int):
    """生成 → 登录控制台 → 触发 AI 创作的完整流程。"""
    result = build_full_workflow(theme=theme, mood=mood, lines=lines)
    click.echo(f"本地已生成：{result['title']}")

    bd = BrowserDriver(headless=ctx.obj["headless"])
    try:
        driver = bd.start()
        console = DouyinMusicConsole(driver)
        console.open()
        if not console.require_login():
            click.echo("登录失败", err=True)
            sys.exit(1)
        ok = console.auto_create_music(prompt=result["prompt"], lyrics=result["lyrics"])
        click.echo(f"AI 创作触发: {'成功' if ok else '失败'}")
        click.prompt("完成，请按回车键关闭浏览器", default=True)
    finally:
        bd.quit()


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
