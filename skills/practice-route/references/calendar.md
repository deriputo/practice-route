# 时间与复测工具

需要按日历排计划时，可以用随技能附带的 Python 3 脚本计算可用时长和复测日期。下面的命令从仓库根目录运行。脚本输出 JSON，由你决定如何更新路线工作表。

```text
python skills/practice-route/scripts/route.py capacity --from 2026-11-09 --through 2026-11-15 --weekly mon=40 --weekly wed=40 --weekly fri=40 --override 2026-11-11=0 --override 2026-11-14=60
```

这个例子有 140 分钟。周三取消，周六临时增加 60 分钟。日期范围包含起止日。日期覆盖替换当日的常规时长，设为 0 代表当天不可用。考试当天不能练习时，把 `--through` 设成考前最后一天。

```text
python skills/practice-route/scripts/route.py review --on 2026-11-09 --through 2026-11-15 --outcome independent --interval 1 --due 2026-11-09 --weekly wed=40 --weekly fri=40
```

这个例子的目标日期是 11 月 12 日，实际可安排的复测是 11 月 13 日。保留目标日期和实际时段，后者可能随日程变化。截止前没有符合条件的时段时，`next_session` 为 `null`。用户可结合剩余时间决定是否提前做短测。

| 作答情况 | 参数 | 日期计算 |
| --- | --- | --- |
| 新项目 | `new` | 从 1 天开始。 |
| 独立完成 | `independent` | 到期后从 1、3、7、14 天中升一档。 |
| 借助完成 | `helped` | 到期后保留当前档。 |
| 未通过 | `missed` | 回到 1 天，使用新题或变更条件验证。 |

提前独立完成或借助完成时保留原目标日期。已有记录时传入原间隔和原目标日期。用户只看了答案或没有提交时，沿用待验证状态。已有自己的复测节奏时按该节奏排期。
