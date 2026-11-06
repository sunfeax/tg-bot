import type { Context } from 'grammy';

export function forceReply(placeholder: string) {
  return {
    reply_markup: { force_reply: true as const, input_field_placeholder: placeholder },
  };
}

export function isReplyTo(prompt: string) {
  return (ctx: Context) => {
    const replied = ctx.message?.reply_to_message;
    return replied?.from?.id === ctx.me.id && replied.text === prompt;
  };
}
