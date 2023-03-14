from collections.abc import Sequence
from datetime import timezone
from io import BytesIO

import matplotlib.pyplot as plt
from nonebot.adapters.onebot.v11 import Bot as BotV11
from nonebot.adapters.onebot.v11 import MessageSegment as MessageSegmentV11
from nonebot.adapters.onebot.v12 import Bot as BotV12
from nonebot.adapters.onebot.v12 import MessageSegment as MessageSegmentV12
from nonebot.params import Arg, Depends
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from nonebot_plugin_datastore import get_session
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.helpers import UserInfo, get_plaintext_content, get_user_info, parse_str

from .. import check_in
from ..helpers import ensure_user
from ..models import BodyFatRecord, DietaryRecord, FitnessRecord, WeightRecord

__plugin_meta__ = PluginMetadata(
    name="打卡历史",
    description="查看打卡历史记录",
    usage="""查看健身打卡历史
/打卡历史 A
查看饮食打卡历史
/打卡历史 B
查看体重和体脂历史
/打卡历史 C""",
    extra={
        "adapters": ["OneBot V11", "OneBot V12"],
    },
)
history_cmd = check_in.command("history", aliases={"打卡历史"})


@history_cmd.handle()
async def handle_first_message(
    state: T_State, content: str = Depends(get_plaintext_content)
):
    state["content"] = content


@history_cmd.got(
    "content",
    prompt="请问你要查询什么历史呢？请输入 A：健身打卡记录 B：饮食打卡记录 C：体重和体脂历史",
    parameterless=[Depends(parse_str("content"))],
)
async def _(
    bot: BotV11 | BotV12,
    content: str = Arg(),
    user_info: UserInfo = Depends(get_user_info),
    session: AsyncSession = Depends(get_session),
):
    content = content.lower()
    if not content:
        await history_cmd.reject("选项不能为空，请重新输入", at_sender=True)

    if content not in ["a", "b", "c"]:
        await history_cmd.reject("选项不正确，请重新输入", at_sender=True)

    user = await ensure_user(session, user_info)

    match content:
        case "a":
            weight_records = (
                await session.scalars(
                    select(FitnessRecord).where(FitnessRecord.user == user)
                )
            ).all()
            if not weight_records:
                await history_cmd.finish("你还没有健身打卡记录哦", at_sender=True)
            msgs = [f"你已成功打卡 {len(weight_records)} 次，以下是你当月的健身情况哦～："]
            for record in weight_records:
                msgs.append(f"{record.time.date()} {record.message}")
            await history_cmd.finish("\n".join(msgs), at_sender=True)
        case "b":
            count = (
                await session.execute(
                    select(DietaryRecord.healthy, func.count("*"))
                    .where(DietaryRecord.user == user)
                    .group_by(DietaryRecord.healthy)
                )
            ).all()
            if not count:
                await history_cmd.finish("你还没有饮食打卡记录哦", at_sender=True)

            healthy_count = next(filter(lambda x: x[0], count), (0, 0))[1]
            unhealthy_count = next(filter(lambda x: not x[0], count), (0, 0))[1]
            total_count = healthy_count + unhealthy_count
            msg = f"你已成功打卡 {total_count} 次，其中健康饮食 {healthy_count} 次，不健康饮食 {unhealthy_count} 次"
            await history_cmd.finish(msg, at_sender=True)
        case "c":
            weight_records = (
                await session.scalars(
                    select(WeightRecord).where(WeightRecord.user == user)
                )
            ).all()
            body_fat_records = (
                await session.scalars(
                    select(BodyFatRecord).where(BodyFatRecord.user == user)
                )
            ).all()
            if not weight_records and not body_fat_records:
                await history_cmd.finish("你还没有体重或体脂记录哦", at_sender=True)

            msg = f"你的目标体重是 {user.target_weight or 'NaN'}kg，目标体脂是 {user.target_body_fat or 'NaN'}%\n"

            image = gerenate_graph(weight_records, body_fat_records)
            if isinstance(bot, BotV11):
                msg += MessageSegmentV11.image(image)
            else:
                file_id = (
                    await bot.upload_file(
                        type="data", data=image, name="weight_body_fat.png"
                    )
                )["file_id"]
                msg += MessageSegmentV12.image(file_id)

            await history_cmd.finish(msg, at_sender=True)


def gerenate_graph(
    weight_records: Sequence[WeightRecord], body_fat_records: Sequence[BodyFatRecord]
) -> bytes:
    weight = {
        record.time.replace(tzinfo=timezone.utc)
        .astimezone()
        .strftime("%Y-%m-%d %H:%M:%S"): record.weight
        for record in weight_records
    }
    body_fat = {
        record.time.replace(tzinfo=timezone.utc)
        .astimezone()
        .strftime("%Y-%m-%d %H:%M:%S"): record.body_fat
        for record in body_fat_records
    }

    fig, (ax0, ax1) = plt.subplots(2, 1, constrained_layout=True)

    ax0.plot(weight.keys(), weight.values())
    ax0.set_title("Weight History")
    ax0.set_xlabel("time")
    ax0.set_ylabel("weight (kg)")

    ax1.plot(body_fat.keys(), body_fat.values())
    ax1.set_title("Body Fat History")
    ax1.set_xlabel("time")
    ax1.set_ylabel("body fat (%)")

    file = BytesIO()
    fig.savefig(file)
    return file.getvalue()
