from __future__ import annotations
import sys
import typing as t

import click
import inflection
import orjson
from bentoml_cli.utils import opt_callback

import openllm

from .. import termui
from ..._prompt import process_prompt

# NOTE: We need to do this so that overload can register
# correct overloads to typing registry
if sys.version_info[:2] >= (3, 11):
    from typing import overload
else:
    from typing_extensions import overload

if t.TYPE_CHECKING:
    from openllm.cli.entrypoint import LiteralOutput

@overload
def cli(model_name: str, prompt: str, format: str | None, output: LiteralOutput, machine: t.Literal[True] = True) -> str: ...
@overload
def cli(model_name: str, prompt: str, format: str | None, output: LiteralOutput, machine: t.Literal[False] = ...) -> None: ...
@click.command("get_prompt", context_settings=termui.CONTEXT_SETTINGS)
@click.argument("model_name", type=click.Choice([inflection.dasherize(name) for name in openllm.CONFIG_MAPPING.keys()]))
@click.argument("prompt", type=click.STRING)
@click.option("-o", "--output", "output", type=click.Choice(["json", "pretty", "porcelain"]), default="pretty", help="Showing output type.", show_default=True, envvar="OPENLLM_OUTPUT", show_envvar=True)
@click.option("--format", type=click.STRING, default=None)
@click.option("--machine", is_flag=True, default=False, hidden=True)
@click.option("--opt", help="Define additional prompt variables. (format: ``--opt system_prompt='You are a useful assistant'``)", required=False, multiple=True, callback=opt_callback, metavar="ARG=VALUE[,ARG=VALUE]")
def cli(model_name: str, prompt: str, format: str | None, output: LiteralOutput, machine: bool, _memoized: dict[str, t.Any], **_: t.Any) -> str | None:
    """Get the default prompt used by OpenLLM."""
    module = openllm.utils.EnvVarMixin(model_name).module
    _memoized = {k: v[0] for k, v in _memoized.items() if v}
    try:
        template = getattr(module, "DEFAULT_PROMPT_TEMPLATE", None)
        prompt_mapping = getattr(module, "PROMPT_MAPPING", None)
        if template is None: raise click.BadArgumentUsage(f"model {model_name} does not have a default prompt template") from None
        if callable(template):
            if format is None:
                if not hasattr(module, "PROMPT_MAPPING") or module.PROMPT_MAPPING is None: raise RuntimeError("Failed to find prompt mapping while DEFAULT_PROMPT_TEMPLATE is a function.")
                raise click.BadOptionUsage("format", f"{model_name} prompt requires passing '--format' (available format: {list(module.PROMPT_MAPPING)})")
            if prompt_mapping is None: raise click.BadArgumentUsage(f"Failed to fine prompt mapping while the default prompt for {model_name} is a callable.") from None
            if format not in prompt_mapping: raise click.BadOptionUsage("format", f"Given format {format} is not valid for {model_name} (available format: {list(prompt_mapping)})")
            _prompt_template = template(format)
        else: _prompt_template = template
        fully_formatted = process_prompt(prompt, _prompt_template, True, **_memoized)
        if machine: return repr(fully_formatted)
        elif output == "porcelain": termui.echo(repr(fully_formatted), fg="white")
        elif output == "json": termui.echo(orjson.dumps({"prompt": fully_formatted}, option=orjson.OPT_INDENT_2).decode(), fg="white")
        else:
            termui.echo(f"== Prompt for {model_name} ==\n", fg="magenta")
            termui.echo(fully_formatted, fg="white")
    except AttributeError: raise click.ClickException(f"Failed to determine a default prompt template for {model_name}.") from None
