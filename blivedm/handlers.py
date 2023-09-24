# -*- coding: utf-8 -*-
import logging
from typing import *

from .clients import ws_base
from .models import web as web_models, open_live as open_models

__all__ = (
    'HandlerInterface',
    'BaseHandler',
)

logger = logging.getLogger('blivedm')

logged_unknown_cmds = {
    'AREA_RANK_CHANGED',
    'ANCHOR_LOT_CHECKSTATUS',  # 天选时刻检查状态
    'ANCHOR_LOT_START',  # 天选时刻抽奖开始
    'ANCHOR_LOT_END',  # 天选时刻抽奖结束
    'ANCHOR_LOT_AWARD',  # 天选时刻中奖名单
    'ANCHOR_HELPER_DANMU',
    'COMBO_SEND',  # 礼物连击
    'COMBO_END',
    'COMMON_NOTICE_DANMAKU',  # 通用通知，含红包礼物涨粉、直播活动信息等
    'CUSTOM_NOTICE_CARD',
    'DANMU_AGGREGATION',  # 抽奖弹幕，包含天选抽奖弹幕、红包抽奖弹幕等
    'ENTRY_EFFECT',  # 入场特效
    'ENTRY_EFFECT_MUST_RECEIVE',
    'FULL_SCREEN_SPECIAL_EFFECT',
    'GIFT_PANEL_PLAN',
    'GIFT_STAR_PROCESS',
    'GUARD_ACHIEVEMENT_ROOM',
    'GUARD_HONOR_THOUSAND',
    'HOT_RANK_CHANGED',
    'HOT_RANK_CHANGED_V2',
    'INTERACT_WORD',
    'LIVE',  # 直播开始
    'LIVE_INTERACTIVE_GAME',
    'LIVE_OPEN_PLATFORM_GAME',
    'LIVE_PANEL_CHANGE_CONTENT',
    'LIKE_INFO_V3_CLICK',  # 用户点赞
    'LIKE_INFO_V3_UPDATE',  # 点赞总数量更新
    'LIKE_INFO_V3_NOTICE',  # 双击点赞提示
    'MESSAGEBOX_USER_GAIN_MEDAL',  # 加入粉丝团？
    'NOTICE_MSG',  # 通知横幅
    'ONLINE_RANK_COUNT',  # 高能用户总数量
    'ONLINE_RANK_TOP3',  # 高能榜前三变化
    'ONLINE_RANK_V2',  # 高能榜前七名单
    'PK_BATTLE_START',
    'PK_BATTLE_START_NEW',
    'PK_BATTLE_PRE_NEW',
    'PK_BATTLE_PRE',
    'PK_BATTLE_END',
    'PK_BATTLE_FINAL_PROCESS',
    'PK_BATTLE_PROCESS',
    'PK_BATTLE_PROCESS_NEW',
    'PK_BATTLE_RANK_CHANGE',
    'PK_BATTLE_SETTLE',
    'PK_BATTLE_SETTLE_USER',
    'PK_BATTLE_SETTLE_V2',
    'PLAYTOGETHER_ICON_CHANGE',
    'POPULAR_RANK_CHANGED',
    'POPULARITY_RED_POCKET_NEW',  # 红包礼物
    'POPULARITY_RED_POCKET_START',  # 红包开抢
    'POPULARITY_RED_POCKET_WINNER_LIST',  # 红包中奖
    'ROOM_REAL_TIME_MESSAGE_UPDATE',  # 粉丝数等更新
    'ROOM_BLOCK_MSG',
    'ROOM_CHANGE',
    'ROOM_SKIN_MSG',
    'SPREAD_ORDER_START',
    'SPREAD_ORDER_OVER',
    'SPREAD_SHOW_FEET',  # 流量包推广
    'SPREAD_SHOW_FEET_V2',  # 流量包推广
    'STOP_LIVE_ROOM_LIST',  # 停播房间列表
    'SUPER_CHAT_MESSAGE_JPN',  # 醒目留言(日)
    'SUPER_CHAT_ENTRANCE',
    'TRADING_SCORE',
    'USER_PANEL_RED_ALARM',
    'USER_TASK_PROGRESS_V2',  # 用户任务？
    'USER_TOAST_MSG',
    'WIDGET_BANNER',  # 小部件横幅
    'WIDGET_GIFT_STAR_PROCESS',
}
"""已打日志的未知cmd"""


class HandlerInterface:
    """
    直播消息处理器接口
    """

    def handle(self, client: ws_base.WebSocketClientBase, command: dict):
        raise NotImplementedError

    def on_client_stopped(self, client: ws_base.WebSocketClientBase, exception: Optional[Exception]):
        """
        当客户端停止时调用。可以在这里close或者重新start
        """


def _make_msg_callback(method_name, message_cls):
    def callback(self: 'BaseHandler', client: ws_base.WebSocketClientBase, command: dict):
        method = getattr(self, method_name)
        return method(client, message_cls.from_command(command['data']))
    return callback


class BaseHandler(HandlerInterface):
    """
    一个简单的消息处理器实现，带消息分发和消息类型转换。继承并重写_on_xxx方法即可实现自己的处理器
    """

    def __danmu_msg_callback(self, client: ws_base.WebSocketClientBase, command: dict):
        return self._on_danmaku(
            client, web_models.DanmakuMessage.from_command(command['info'], command.get('dm_v2', ''))
        )

    _CMD_CALLBACK_DICT: Dict[
        str,
        Optional[Callable[
            ['BaseHandler', ws_base.WebSocketClientBase, dict],
            Any
        ]]
    ] = {
        # 收到心跳包，这是blivedm自造的消息，原本的心跳包格式不一样
        '_HEARTBEAT': _make_msg_callback('_on_heartbeat', web_models.HeartbeatMessage),
        # 收到弹幕
        # go-common\app\service\live\live-dm\service\v1\send.go
        'DANMU_MSG': __danmu_msg_callback,
        # 有人送礼
        'SEND_GIFT': _make_msg_callback('_on_gift', web_models.GiftMessage),
        # 有人上舰
        'GUARD_BUY': _make_msg_callback('_on_buy_guard', web_models.GuardBuyMessage),
        # 醒目留言
        'SUPER_CHAT_MESSAGE': _make_msg_callback('_on_super_chat', web_models.SuperChatMessage),
        # 删除醒目留言
        'SUPER_CHAT_MESSAGE_DELETE': _make_msg_callback('_on_super_chat_delete', web_models.SuperChatDeleteMessage),
        # 观看人数变化
        'WATCHED_CHANGE': _make_msg_callback('_on_watched', web_models.WatchedMessage),

        #
        # 开放平台消息
        #

        # 收到弹幕
        'LIVE_OPEN_PLATFORM_DM': _make_msg_callback('_on_open_live_danmaku', open_models.DanmakuMessage),
        # 有人送礼
        'LIVE_OPEN_PLATFORM_SEND_GIFT': _make_msg_callback('_on_open_live_gift', open_models.GiftMessage),
        # 有人上舰
        'LIVE_OPEN_PLATFORM_GUARD': _make_msg_callback('_on_open_live_buy_guard', open_models.GuardBuyMessage),
        # 醒目留言
        'LIVE_OPEN_PLATFORM_SUPER_CHAT': _make_msg_callback('_on_open_live_super_chat', open_models.SuperChatMessage),
        # 删除醒目留言
        'LIVE_OPEN_PLATFORM_SUPER_CHAT_DEL': _make_msg_callback(
            '_on_open_live_super_chat_delete', open_models.SuperChatDeleteMessage
        ),
        # 点赞
        'LIVE_OPEN_PLATFORM_LIKE': _make_msg_callback('_on_open_live_like', open_models.LikeMessage),
    }
    """cmd -> 处理回调"""

    def handle(self, client: ws_base.WebSocketClientBase, command: dict):
        cmd = command.get('cmd', '')
        pos = cmd.find(':')  # 2019-5-29 B站弹幕升级新增了参数
        if pos != -1:
            cmd = cmd[:pos]

        if cmd not in self._CMD_CALLBACK_DICT:
            # 只有第一次遇到未知cmd时打日志
            if cmd not in logged_unknown_cmds:
                logger.warning('room=%d unknown cmd=%s, command=%s', client.room_id, cmd, command)
                logged_unknown_cmds.add(cmd)
            return

        callback = self._CMD_CALLBACK_DICT[cmd]
        if callback is not None:
            callback(self, client, command)

    def _on_heartbeat(self, client: ws_base.WebSocketClientBase, message: web_models.HeartbeatMessage):
        """
        收到心跳包
        """

    def _on_danmaku(self, client: ws_base.WebSocketClientBase, message: web_models.DanmakuMessage):
        """
        收到弹幕
        """

    def _on_gift(self, client: ws_base.WebSocketClientBase, message: web_models.GiftMessage):
        """
        收到礼物
        """

    def _on_buy_guard(self, client: ws_base.WebSocketClientBase, message: web_models.GuardBuyMessage):
        """
        有人上舰
        """

    def _on_super_chat(self, client: ws_base.WebSocketClientBase, message: web_models.SuperChatMessage):
        """
        醒目留言
        """

    def _on_super_chat_delete(
        self, client: ws_base.WebSocketClientBase, message: web_models.SuperChatDeleteMessage
    ):
        """
        删除醒目留言
        """

    def _on_watched(self, client: ws_base.WebSocketClientBase, message: web_models.WatchedMessage):
        """
        观看人数变化
        """

    #
    # 开放平台消息
    #

    def _on_open_live_danmaku(self, client: ws_base.WebSocketClientBase, message: open_models.DanmakuMessage):
        """
        收到弹幕
        """

    def _on_open_live_gift(self, client: ws_base.WebSocketClientBase, message: open_models.GiftMessage):
        """
        收到礼物
        """

    def _on_open_live_buy_guard(self, client: ws_base.WebSocketClientBase, message: open_models.GuardBuyMessage):
        """
        有人上舰
        """

    def _on_open_live_super_chat(
        self, client: ws_base.WebSocketClientBase, message: open_models.SuperChatMessage
    ):
        """
        醒目留言
        """

    def _on_open_live_super_chat_delete(
        self, client: ws_base.WebSocketClientBase, message: open_models.SuperChatDeleteMessage
    ):
        """
        删除醒目留言
        """

    def _on_open_live_like(self, client: ws_base.WebSocketClientBase, message: open_models.LikeMessage):
        """
        点赞
        """
