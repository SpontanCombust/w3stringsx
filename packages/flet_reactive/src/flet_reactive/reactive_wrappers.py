from typing import Dict, Callable, Any, Iterable, MutableSequence, SupportsIndex, TypeVar, final, List, Sequence, Generic, cast

import flet as ft
from flet.core.text_style import StrutStyle
from flet.core.gradients import Gradient
from flet.core.text import TextSelectionChangeEvent
import flet_datatable2 as ftdt2
from flet_datatable2.datacolumn2 import DataColumnSortEvent

from flet_reactive.state import State, ListState
from flet_reactive.state_observer import StateObserver, ListStateObserver


_T = TypeVar('_T')
_C = TypeVar('_C', bound=ft.Control)

def _unwrap_value(v: _T | State[_T]) -> _T:
    if isinstance(v, State):
        return v.value
    else:
        return v

@final
class _StatefulPropertyBinding(StateObserver[_T]):
    def __init__(self, state: State[_T], target_ctrl: ft.Control, target_prop_name: str) -> None:
        self.state = state
        self.target_ctrl = target_ctrl
        self.target_prop = target_prop_name

    def setup_observed_states(self):
        self.state.add_observer(self)

    def release_observed_states(self) -> None:
        self.state.remove_observer(self)

    def on_state_changed(self, old_state: _T, new_state: _T) -> None:
        setattr(self.target_ctrl, self.target_prop, new_state)
        self.target_ctrl.update()

    def sync_state(self) -> None:
        self.state.value = getattr(self.target_ctrl, self.target_prop)


class _StatefulCtrlSequencePropertyBinding(Generic[_T, _C], ListStateObserver[_T]):
    def __init__(self, 
        state: ListState[_T], 
        state_ctrl_mapper: Callable[[_T, int], _C], 
        target_ctrl: ft.Control, 
        target_ctrl_seq: MutableSequence[_C]
    ) -> None:
        self.state = state
        self.state_ctrl_mapper = state_ctrl_mapper
        self.target_ctrl = target_ctrl
        self.target_ctrl_seq = target_ctrl_seq

        for i in range(len(state)):
            target_ctrl_seq.insert(i, state_ctrl_mapper(state[i], i))

    def setup_observed_states(self):
        self.state.add_observer(self)

    def release_observed_states(self) -> None:
        self.state.remove_observer(self)

    def on_set_state_item(self, key: SupportsIndex, value: _T) -> None:
        self.target_ctrl_seq.__setitem__(int(key), self.state_ctrl_mapper(value, int(key)))
        self.target_ctrl.update()

    def on_set_state_item_slice(self, key: slice, value: Iterable[_T]) -> None:
        self.target_ctrl_seq.__setitem__(key, [self.state_ctrl_mapper(value, i) for value, i in zip(value, range(key.start, key.stop))])
        self.target_ctrl.update()

    def on_del_state_item(self, key: SupportsIndex) -> None:
        self.target_ctrl_seq.__delitem__(int(key))
        self.target_ctrl.update()

    def on_del_state_item_slice(self, key: slice) -> None:
        self.target_ctrl_seq.__delitem__(key)
        self.target_ctrl.update()

    def on_insert_state_item(self, key: SupportsIndex, value: _T) -> None:
        self.target_ctrl_seq.insert(int(key), self.state_ctrl_mapper(value, int(key)))
        self.target_ctrl.update()

class _StatefulDataRowsPropertyBinding(_StatefulCtrlSequencePropertyBinding[_T, ftdt2.DataRow2]):
    def __init__(self, 
        state: ListState[_T], 
        state_ctrl_mapper: Callable[[_T, int], ftdt2.DataRow2], 
        target_ctrl: ft.Control, 
        target_ctrl_seq: MutableSequence[ftdt2.DataRow2],
        column_count: int,
        placeholder_count: int
    ) -> None:
        super().__init__(state, state_ctrl_mapper, target_ctrl, target_ctrl_seq)
        self.column_count = column_count
        self.placeholder_count = placeholder_count
        self.placeholder_ctrl_factory = lambda: ftdt2.DataRow2(
            cells=[
                ft.DataCell(ft.Text(), placeholder=True)
                for i in range(column_count)
            ],
            data='placeholder'
        )

        # fill placeholders
        if placeholder_count > len(state):
            for i in range(placeholder_count - len(state)):
                target_ctrl_seq.append(self.placeholder_ctrl_factory())


    def on_set_state_item(self, key: SupportsIndex, value: _T) -> None:
        return super().on_set_state_item(key, value)

    def on_set_state_item_slice(self, key: slice, value: Iterable[_T]) -> None:
        return super().on_set_state_item_slice(key, value)

    def on_del_state_item(self, key: SupportsIndex) -> None:
        seq_idx = int(key)
        seq_idx = seq_idx if seq_idx >= 0 else len(self.state) + 1 + seq_idx
        # within the controls sequence there is more elements than in the data/state list
        # due to said sequence being filled with placeholders to a certain threshold
        # if a deleted index in the data list falls below that threshold
        # corresponding control has tp be replaced with a placeholder instead of being outright removed
        # if it goes beyond the threshold, it can be simply removed 
        if seq_idx < self.placeholder_count:
            self.target_ctrl_seq.__setitem__(seq_idx, self.placeholder_ctrl_factory())
        else:
            self.target_ctrl_seq.__delitem__(seq_idx)
        self.target_ctrl.update()

    def on_del_state_item_slice(self, key: slice) -> None:
        raise NotImplementedError()
        # idx_range = range(key.start, key.stop, key.step)
        # for idx in idx_range:
        #     idx = idx if idx >= 0 else len(self.state) + idx_range.count() - idx
        #     if idx < self.placeholder_count:
        #         self.target_ctrl_seq.__setitem__(idx, copy(self.placeholder_ctrl))
        #     else:
        #         self.target_ctrl_seq.__delitem__(int(idx))
        # self.target_ctrl.update()

    def on_insert_state_item(self, key: SupportsIndex, value: _T) -> None:
        seq_idx = int(key)
        seq_idx = seq_idx if seq_idx >= 0 else len(self.state) + seq_idx
        mapped = self.state_ctrl_mapper(value, seq_idx)
        if seq_idx < self.placeholder_count and self.target_ctrl_seq[seq_idx].data == 'placeholder':
            self.target_ctrl_seq.__setitem__(seq_idx, mapped)
        else:
            self.target_ctrl_seq.insert(seq_idx, mapped)
        self.target_ctrl.update()


class _ReactiveControlWrapper:
    def __init__(self) -> None:
        self.__prop_bindings = list[_StatefulPropertyBinding | _StatefulCtrlSequencePropertyBinding | _StatefulDataRowsPropertyBinding]()

    def _new_stateful_prop_binding(self, 
        state: State[_T], 
        target_ctrl: ft.Control, 
        target_prop_name: str
    ) -> _StatefulPropertyBinding:
        binding = _StatefulPropertyBinding(state, target_ctrl, target_prop_name)
        self.__prop_bindings.append(binding)
        return binding
    
    def _new_stateful_ctrl_seq_prop_binding(self, 
        state: ListState[_T], 
        state_ctrl_mapper: Callable[[_T, int], _C], 
        target_ctrl: ft.Control, 
        target_ctrl_seq: MutableSequence[_C]
    ) -> _StatefulCtrlSequencePropertyBinding:
        binding = _StatefulCtrlSequencePropertyBinding(state, state_ctrl_mapper, target_ctrl, target_ctrl_seq)
        self.__prop_bindings.append(binding)
        return binding
    
    def _new_stateful_data_rows_prop_binding(self, 
        state: ListState[_T], 
        state_ctrl_mapper: Callable[[_T, int], ftdt2.DataRow2], 
        target_ctrl: ft.Control, 
        target_ctrl_seq: MutableSequence[ftdt2.DataRow2],
        column_count: int,
        placeholder_count: int
    ) -> _StatefulDataRowsPropertyBinding:
        binding = _StatefulDataRowsPropertyBinding(state, state_ctrl_mapper, target_ctrl, target_ctrl_seq, column_count, placeholder_count)
        self.__prop_bindings.append(binding)
        return binding

    def _init_prop_bindings(self):
        for pso in self.__prop_bindings:
            pso.setup_observed_states()

    def _drop_prop_bindings(self):
        for pso in self.__prop_bindings:
            pso.release_observed_states()


"""
Standard Flet controls supplied with reactive properties.
These get added as they're demanded.
"""

class ReactiveCheckbox(ft.Checkbox, _ReactiveControlWrapper):
    def __init__(self, 
        label: str | ft.Control | None = None, 
        value: bool | None | State[bool | None] = None, 
        label_position: ft.LabelPosition | None = None, 
        label_style: ft.TextStyle | None = None, 
        tristate: bool | None = None, 
        autofocus: bool | None = None, 
        fill_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        overlay_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        check_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        active_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        hover_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        focus_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        semantics_label: str | None = None, 
        shape: ft.OutlinedBorder | None = None, 
        splash_radius: int | float | None = None, 
        border_side: None | ft.BorderSide | Dict[ft.ControlState, ft.BorderSide] = None, 
        is_error: bool | None = None, visual_density: ft.VisualDensity | None = None, 
        mouse_cursor: ft.MouseCursor | None = None, 
        on_change: Callable[[ft.ControlEvent], Any] | None = None, 
        on_focus: Callable[[ft.ControlEvent], Any] | None = None, 
        on_blur: Callable[[ft.ControlEvent], Any] | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None | State[bool | None] = None, 
        data: Any = None, 
        adaptive: bool | None = None
    ):
        super().__init__(
            label, 
            _unwrap_value(value), 
            label_position, 
            label_style, 
            tristate, 
            autofocus, 
            fill_color, 
            overlay_color, 
            check_color, 
            active_color, 
            hover_color, 
            focus_color, 
            semantics_label, 
            shape, 
            splash_radius, 
            border_side, 
            is_error, 
            visual_density, 
            mouse_cursor, 
            on_change, 
            on_focus, 
            on_blur, 
            ref, 
            key, 
            width, 
            height, 
            left, 
            top, 
            right, 
            bottom, 
            expand, 
            expand_loose, 
            col, 
            opacity, 
            rotate, 
            scale, 
            offset, 
            aspect_ratio, 
            animate_opacity, 
            animate_size, 
            animate_position, 
            animate_rotation, 
            animate_scale, 
            animate_offset, 
            on_animation_end, 
            tooltip, 
            badge, 
            visible, 
            _unwrap_value(disabled), 
            data, 
            adaptive
        )

        if isinstance(value, State):
            binding = self._new_stateful_prop_binding(value, self, 'value')
            self.on_change = lambda ev: (
                binding.sync_state(),
                on_change(ev) if on_change else None
            )
        if isinstance(disabled, State):
            self._new_stateful_prop_binding(disabled, self, 'disabled')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveTextField(ft.TextField, _ReactiveControlWrapper):
    def __init__(self, 
        value: str | None | State[str | None] = None, 
        keyboard_type: ft.KeyboardType | None = None, 
        multiline: bool | None = None, 
        min_lines: int | None = None, 
        max_lines: int | None = None, 
        max_length: int | None = None, 
        password: bool | None = None, 
        can_reveal_password: bool | None = None, 
        read_only: bool | None = None, 
        shift_enter: bool | None = None, 
        text_align: ft.TextAlign | None = None, 
        autofocus: bool | None = None, 
        capitalization: ft.TextCapitalization | None = None, 
        autocorrect: bool | None = None, 
        enable_suggestions: bool | None = None, 
        smart_dashes_type: bool | None = None, 
        smart_quotes_type: bool | None = None, 
        show_cursor: bool | None = None, 
        cursor_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        cursor_error_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        cursor_width: int | float | None = None, 
        cursor_height: int | float | None = None, 
        cursor_radius: int | float | None = None, 
        selection_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        input_filter: ft.InputFilter | None = None, 
        obscuring_character: str | None = None, 
        enable_interactive_selection: bool | None = None, 
        enable_ime_personalized_learning: bool | None = None, 
        can_request_focus: bool | None = None, 
        ignore_pointers: bool | None = None, 
        enable_scribble: bool | None = None, 
        animate_cursor_opacity: bool | None = None, 
        always_call_on_tap: bool | None = None, 
        scroll_padding: int | float | ft.Padding | None = None, 
        clip_behavior: ft.ClipBehavior | None = None, 
        keyboard_brightness: ft.Brightness | None = None, 
        mouse_cursor: ft.MouseCursor | None = None, 
        strut_style: StrutStyle | None = None, 
        autofill_hints: None | ft.AutofillHint | List[ft.AutofillHint] = None, 
        on_change: Callable[[ft.ControlEvent], Any] | None = None, 
        on_click: Callable[[ft.ControlEvent], Any] | None = None, 
        on_submit: Callable[[ft.ControlEvent], Any] | None = None, 
        on_focus: Callable[[ft.ControlEvent], Any] | None = None, 
        on_blur: Callable[[ft.ControlEvent], Any] | None = None, 
        on_tap_outside: Callable[[ft.ControlEvent], Any] | None = None, 
        text_size: int | float | None = None, 
        text_style: ft.TextStyle | None = None, 
        text_vertical_align: ft.VerticalAlignment | int | float | None = None, 
        label: str | ft.Control | None = None, 
        label_style: ft.TextStyle | None = None, 
        icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None, 
        border: ft.InputBorder | None = None, 
        color: str | ft.Colors | ft.CupertinoColors | None = None, 
        bgcolor: str | ft.Colors | ft.CupertinoColors | None = None, 
        border_radius: int | float | ft.BorderRadius | None = None, 
        border_width: int | float | None = None, 
        border_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        focused_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        focused_bgcolor: str | ft.Colors | ft.CupertinoColors | None = None, 
        focused_border_width: int | float | None = None, 
        focused_border_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        content_padding: int | float | ft.Padding | None = None, 
        dense: bool | None = None, 
        filled: bool | None = None, 
        fill_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        hover_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        hint_text: str | None = None, 
        hint_style: ft.TextStyle | None = None, 
        helper: ft.Control | None = None, 
        helper_text: str | None = None, 
        helper_style: ft.TextStyle | None = None, 
        counter: ft.Control | None = None, 
        counter_text: str | None = None, 
        counter_style: ft.TextStyle | None = None, 
        error: ft.Control | None = None, 
        error_text: str | None = None, 
        error_style: ft.TextStyle | None = None, 
        prefix: ft.Control | None = None, 
        prefix_icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None, 
        prefix_text: str | None = None, 
        prefix_style: ft.TextStyle | None = None, 
        suffix: ft.Control | None = None, 
        suffix_icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None, 
        suffix_text: str | None = None, 
        suffix_style: ft.TextStyle | None = None, 
        focus_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        align_label_with_hint: bool | None = None, 
        hint_fade_duration: int | ft.Duration | None = None, 
        hint_max_lines: int | None = None, 
        helper_max_lines: int | None = None, 
        error_max_lines: int | None = None, 
        prefix_icon_size_constraints: ft.BoxConstraints | None = None, 
        suffix_icon_size_constraints: ft.BoxConstraints | None = None, 
        size_constraints: ft.BoxConstraints | None = None, 
        collapsed: bool | None = None, 
        fit_parent_size: bool | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None = None, 
        data: Any = None, 
        rtl: bool | None = None, 
        adaptive: bool | None = None
    ):
        super().__init__(
            _unwrap_value(value),
            keyboard_type,
            multiline,
            min_lines,
            max_lines,
            max_length,
            password,
            can_reveal_password,
            read_only,
            shift_enter,
            text_align,
            autofocus,
            capitalization,
            autocorrect,
            enable_suggestions,
            smart_dashes_type,
            smart_quotes_type,
            show_cursor,
            cursor_color,
            cursor_error_color,
            cursor_width,
            cursor_height,
            cursor_radius,
            selection_color,
            input_filter,
            obscuring_character,
            enable_interactive_selection,
            enable_ime_personalized_learning,
            can_request_focus,
            ignore_pointers,
            enable_scribble,
            animate_cursor_opacity,
            always_call_on_tap,
            scroll_padding,
            clip_behavior,
            keyboard_brightness,
            mouse_cursor,
            strut_style,
            autofill_hints,
            on_change,
            on_click,
            on_submit,
            on_focus,
            on_blur,
            on_tap_outside,
            text_size,
            text_style,
            text_vertical_align,
            label,
            label_style,
            icon,
            border,
            color,
            bgcolor,
            border_radius,
            border_width,
            border_color,
            focused_color,
            focused_bgcolor,
            focused_border_width,
            focused_border_color,
            content_padding,
            dense,
            filled,
            fill_color,
            hover_color,
            hint_text,
            hint_style,
            helper,
            helper_text,
            helper_style,
            counter,
            counter_text,
            counter_style,
            error,
            error_text,
            error_style,
            prefix,
            prefix_icon,
            prefix_text,
            prefix_style,
            suffix,
            suffix_icon,
            suffix_text,
            suffix_style,
            focus_color,
            align_label_with_hint,
            hint_fade_duration,
            hint_max_lines,
            helper_max_lines,
            error_max_lines,
            prefix_icon_size_constraints,
            suffix_icon_size_constraints,
            size_constraints,
            collapsed,
            fit_parent_size,
            ref,
            key,
            width,
            height,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            tooltip,
            badge,
            visible,
            disabled,
            data,
            rtl,
            adaptive
        )

        if isinstance(value, State):
            binding = self._new_stateful_prop_binding(value, self, 'value')
            self.on_change = lambda ev: (
                binding.sync_state(),
                on_change(ev) if on_change else None
            )

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()


class ReactiveFilledButton(ft.FilledButton, _ReactiveControlWrapper):
    def __init__(self, 
        text: str | None = None, 
        icon: str | ft.Icons | ft.CupertinoIcons | None = None, 
        icon_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        color: str | ft.Colors | ft.CupertinoColors | None = None, 
        bgcolor: str | ft.Colors | ft.CupertinoColors | None = None, 
        content: ft.Control | None = None, 
        elevation: int | float | None = None, 
        style: ft.ButtonStyle | None = None, 
        autofocus: bool | None = None, 
        clip_behavior: ft.ClipBehavior | None = None, 
        url: str | None = None, 
        url_target: ft.UrlTarget | None = None, 
        on_click: Callable[[ft.ControlEvent], Any] | None = None, 
        on_long_press: Callable[[ft.ControlEvent], Any] | None = None, 
        on_hover: Callable[[ft.ControlEvent], Any] | None = None, 
        on_focus: Callable[[ft.ControlEvent], Any] | None = None, 
        on_blur: Callable[[ft.ControlEvent], Any] | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None | State[bool | None] = None, 
        data: Any = None, 
        adaptive: bool | None = None
    ):
        super().__init__(
            text, 
            icon, 
            icon_color, 
            color, 
            bgcolor, 
            content, 
            elevation, 
            style, 
            autofocus, 
            clip_behavior, 
            url, 
            url_target, 
            on_click, 
            on_long_press, 
            on_hover, 
            on_focus, 
            on_blur, 
            ref, 
            key, 
            width, 
            height, 
            left, 
            top, 
            right, 
            bottom, 
            expand, 
            expand_loose, 
            col, 
            opacity, 
            rotate, 
            scale, 
            offset, 
            aspect_ratio, 
            animate_opacity, 
            animate_size, 
            animate_position, 
            animate_rotation, 
            animate_scale, 
            animate_offset, 
            on_animation_end, 
            tooltip, 
            badge, 
            visible, 
            _unwrap_value(disabled), 
            data, 
            adaptive
        )

        if isinstance(disabled, State):
            self._new_stateful_prop_binding(disabled, self, 'disabled')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveDataColumn(ftdt2.DataColumn2, _ReactiveControlWrapper):
    def __init__(self, 
        label: ft.Control, 
        size: ftdt2.Size | None = None, 
        numeric: bool | None = None, 
        tooltip: str | None = None, 
        fixed_width: int | float | None = None, 
        heading_row_alignment: ft.MainAxisAlignment | None = None, 
        on_sort: ft.OptionalEventCallable[DataColumnSortEvent] = None, 
        ref=None, 
        visible: bool | None = None, 
        disabled: bool | None = None, 
        data: Any = None
    ):
        super().__init__(
            label, 
            size, 
            numeric, 
            tooltip, 
            fixed_width, 
            heading_row_alignment, 
            on_sort, 
            ref, 
            visible, 
            disabled, 
            data
        )

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()

class ReactiveDataRow(ftdt2.DataRow2, _ReactiveControlWrapper):
    def __init__(self, 
        cells: List[ft.DataCell], 
        color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None,
        decoration: ft.BoxDecoration | None = None,
        specific_row_height: int | float | None = None,
        selected: bool | None | State[bool | None] = None,
        on_long_press: Callable[[ft.ControlEvent], Any] | None = None,
        on_select_changed: Callable[[ft.ControlEvent], Any] | None = None,
        on_double_tap: Callable[[ft.ControlEvent], Any] | None = None,
        on_secondary_tap: Callable[[ft.ControlEvent], Any] | None = None,
        on_secondary_tap_down: Callable[[ft.ControlEvent], Any] | None = None,
        on_tap: Callable[[ft.ControlEvent], Any] | None = None,
        ref=None,
        visible: bool | None = None,
        disabled: bool | None = None, 
        data: Any = None
    ):
        super().__init__(
            cells,
            color,
            decoration,
            specific_row_height,
            _unwrap_value(selected), 
            on_long_press,
            on_select_changed,
            on_double_tap,
            on_secondary_tap,
            on_secondary_tap_down,
            on_tap,
            ref,
            visible,
            disabled,
            data
        )

        if isinstance(selected, State):
            binding = self._new_stateful_prop_binding(selected, self, 'selected')
            self.on_select_changed = lambda ev: (
                binding.sync_state(),
                on_select_changed(ev) if on_select_changed else None
            )

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()

class ReactiveDataTable(ftdt2.DataTable2, _ReactiveControlWrapper, Generic[_T]):
    def __init__(self, 
        columns: Sequence[ReactiveDataColumn], 
        rows_data: ListState[_T] | None = None,
        rows_mapper: Callable[[_T, int], ReactiveDataRow] | None = None,
        placeholder_rows_count: int | None = None,
        rows: Sequence[ReactiveDataRow] | None = None, 
        empty: ft.Control | None = None, 
        bottom_margin: int | float | None = None, 
        lm_ratio: int | float | None = None, 
        sm_ratio: int | float | None = None, 
        fixed_left_columns: int | None = None, 
        fixed_top_rows: int | None = None, 
        fixed_columns_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        fixed_corner_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        min_width: int | float | None = None, 
        sort_ascending: bool | None = None, 
        show_checkbox_column: bool | None = None, 
        show_heading_checkbox: bool | None = None, 
        heading_checkbox_theme: ft.CheckboxTheme | None = None, 
        data_row_checkbox_theme: ft.CheckboxTheme | None = None, 
        sort_column_index: int | None = None, 
        sort_arrow_icon: str | ft.Icons | ft.CupertinoIcons | None = None, 
        sort_arrow_animation_duration: int | ft.Duration | None = None, 
        show_bottom_border: bool | None = None, 
        is_horizontal_scroll_bar_visible: bool | None = None, 
        is_vertical_scroll_bar_visible: bool | None = None, 
        border: ft.Border | None = None, 
        border_radius: int | float | ft.BorderRadius | None = None, 
        horizontal_lines: ft.BorderSide | None = None, 
        vertical_lines: ft.BorderSide | None = None, 
        checkbox_horizontal_margin: int | float | None = None, 
        checkbox_alignment: ft.Alignment | None = None, 
        column_spacing: int | float | None = None, 
        data_row_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        data_row_height: int | float | None = None, 
        data_text_style: ft.TextStyle | None = None, 
        bgcolor: str | ft.Colors | ft.CupertinoColors | None = None, 
        gradient: Gradient | None = None, 
        divider_thickness: int | float | None = None, 
        heading_row_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        heading_row_height: int | float | None = None, 
        heading_text_style: ft.TextStyle | None = None, 
        heading_row_decoration: ft.BoxDecoration | None = None, 
        horizontal_margin: int | float | None = None, 
        clip_behavior: ft.ClipBehavior | None = None, 
        on_select_all: Callable[[ft.ControlEvent], Any] | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None = None, 
        data: Any = None
    ):
        super().__init__(
            list(columns),
            list(rows) if rows is not None else None,
            empty,
            bottom_margin,
            lm_ratio,
            sm_ratio,
            fixed_left_columns,
            fixed_top_rows,
            fixed_columns_color,
            fixed_corner_color,
            min_width,
            sort_ascending,
            show_checkbox_column,
            show_heading_checkbox,
            heading_checkbox_theme,
            data_row_checkbox_theme,
            sort_column_index,
            sort_arrow_icon,
            sort_arrow_animation_duration,
            show_bottom_border,
            is_horizontal_scroll_bar_visible,
            is_vertical_scroll_bar_visible,
            border,
            border_radius,
            horizontal_lines,
            vertical_lines,
            checkbox_horizontal_margin,
            checkbox_alignment,
            column_spacing,
            data_row_color,
            data_row_height,
            data_text_style,
            bgcolor,
            gradient,
            divider_thickness,
            heading_row_color,
            heading_row_height,
            heading_text_style,
            heading_row_decoration,
            horizontal_margin,
            clip_behavior,
            on_select_all,
            ref,
            key,
            width,
            height,
            left,
            top,
            right,
            bottom,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            tooltip,
            badge,
            visible,
            disabled,
            data
        )

        if rows_data is not None and rows_mapper is not None:
            self.rows = []
            some_rows = cast(list[ftdt2.DataRow2], self.rows) # promise type-cheker it won't be None

            if placeholder_rows_count is not None and placeholder_rows_count > 0:
                column_count = len(columns)
                self._new_stateful_data_rows_prop_binding(rows_data, rows_mapper, self, some_rows, column_count, placeholder_rows_count)
            else:
                self._new_stateful_ctrl_seq_prop_binding(rows_data, rows_mapper, self, some_rows)

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveColumn(ft.Column, _ReactiveControlWrapper, Generic[_T]):
    def __init__(self,
        controls: Sequence[ft.Control] | None = None,
        controls_data: ListState[_T] | None = None,
        controls_mapper: Callable[[_T, int], ft.Control] | None = None,
        alignment: ft.MainAxisAlignment | None = None,
        horizontal_alignment: ft.CrossAxisAlignment | None = None,
        spacing: int | float | None = None,
        tight: bool | None = None,
        wrap: bool | None = None,
        run_spacing: int | float | None = None,
        run_alignment: ft.MainAxisAlignment | None = None,
        ref: ft.Ref | None = None,
        key: str | None = None,
        width: int | float | None = None,
        height: int | float | None | State[int | float | None] = None,
        left: int | float | None = None,
        top: int | float | None = None,
        right: int | float | None = None,
        bottom: int | float | None = None,
        expand: None | bool | int = None,
        expand_loose: bool | None = None,
        col: Dict[str, int | float] | int | float | None = None,
        opacity: int | float | None = None,
        rotate: int | float | ft.Rotate | None = None,
        scale: int | float | ft.Scale | None = None,
        offset: ft.Offset | None = None,
        aspect_ratio: int | float | None = None,
        animate_opacity: bool | int | ft.Animation | None = None,
        animate_size: bool | int | ft.Animation | None = None,
        animate_position: bool | int | ft.Animation | None = None,
        animate_rotation: bool | int | ft.Animation | None = None,
        animate_scale: bool | int | ft.Animation | None = None,
        animate_offset: bool | int | ft.Animation | None = None,
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None,
        visible: bool | None = None,
        disabled: bool | None = None,
        data: Any = None,
        rtl: bool | None = None,
        scroll: ft.ScrollMode | None = None,
        auto_scroll: bool | None = None,
        on_scroll_interval: int | float | None = None, 
        on_scroll: Callable[[ft.OnScrollEvent], None] | None = None,
        adaptive: bool | None = None
    ):
        super().__init__(
            controls,
            alignment,
            horizontal_alignment,
            spacing,
            tight,
            wrap,
            run_spacing,
            run_alignment,
            ref,
            key,
            width,
            _unwrap_value(height),
            left,
            top,
            right,
            bottom,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            visible,
            disabled,
            data,
            rtl,
            scroll,
            auto_scroll,
            on_scroll_interval,
            on_scroll,
            adaptive
        )

        if controls_data is not None and controls_mapper is not None:
            self.controls = []
            self._new_stateful_ctrl_seq_prop_binding(controls_data, controls_mapper, self, self.controls)
        if isinstance(height, State):
            self._new_stateful_prop_binding(height, self, 'height')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveContainer(ft.Container, _ReactiveControlWrapper):
    def __init__(self, 
        content: ft.Control | None = None, 
        padding: int | float | ft.Padding | None = None, 
        margin: int | float | ft.Margin | None = None, 
        alignment: ft.Alignment | None = None,
        bgcolor: str | ft.Colors | ft.CupertinoColors | None | State[str | ft.Colors | ft.CupertinoColors | None] = None,
        gradient: Gradient | None = None,
        blend_mode: ft.BlendMode | None = None,
        border: ft.Border | None | State[ft.Border | None] = None,
        border_radius: int | float | ft.BorderRadius | None = None,
        shape: ft.BoxShape | None = None,
        clip_behavior: ft.ClipBehavior | None = None,
        ink: bool | None = None,
        image: ft.DecorationImage | None = None,
        ink_color: str | ft.Colors | ft.CupertinoColors | None = None,
        animate: bool | int | ft.Animation | None = None,
        blur: None | float | int | ft.Blur = None,
        shadow: None | ft.BoxShadow | List[ft.BoxShadow] = None,
        url: str | None = None,
        url_target: ft.UrlTarget | None = None,
        theme: ft.Theme | None = None,
        dark_theme: ft.Theme | None = None,
        theme_mode: ft.ThemeMode | None = None,
        color_filter: ft.ColorFilter | None = None,
        ignore_interactions: bool | None = None,
        foreground_decoration: ft.BoxDecoration | None = None,
        on_click: Callable[[ft.ControlEvent], Any] | None = None,
        on_tap_down: Callable[[ft.ContainerTapEvent], Any] | None = None,
        on_long_press: Callable[[ft.ControlEvent], Any] | None = None,
        on_hover: Callable[[ft.ControlEvent], Any] | None = None,
        ref: ft.Ref | None = None,
        key: str | None = None,
        width: int | float | None = None,
        height: int | float | None | State[int | float | None] = None,
        left: int | float | None = None,
        top: int | float | None = None,
        right: int | float | None = None,
        bottom: int | float | None = None,
        expand: None | bool | int = None,
        expand_loose: bool | None = None,
        col: Dict[str, int | float] | int | float | None = None,
        opacity: int | float | None | State[int | float | None] = None,
        rotate: int | float | ft.Rotate | None = None,
        scale: int | float | ft.Scale | None = None,
        offset: ft.Offset |  None = None,
        aspect_ratio: int | float | None = None,
        animate_opacity: bool | int | ft.Animation | None = None,
        animate_size: bool | int | ft.Animation | None = None,
        animate_position: bool | int | ft.Animation | None = None,
        animate_rotation: bool | int | ft.Animation | None = None,
        animate_scale: bool | int | ft.Animation | None = None,
        animate_offset: bool | int | ft.Animation | None = None,
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None,
        tooltip: str | ft.Tooltip | None = None,
        badge: str | ft.Badge | None = None,
        visible: bool | None = None,
        disabled: bool | None | State[bool | None] = None,
        data: Any = None,
        rtl: bool | None = None,
        adaptive: bool | None = None
    ):
        super().__init__(
            content,
            padding,
            margin, 
            alignment,
            _unwrap_value(bgcolor),
            gradient,
            blend_mode,
            _unwrap_value(border),
            border_radius,
            shape,
            clip_behavior,
            ink,
            image,
            ink_color,
            animate,
            blur,
            shadow,
            url,
            url_target,
            theme,
            dark_theme,
            theme_mode,
            color_filter,
            ignore_interactions,
            foreground_decoration,
            on_click,
            on_tap_down,
            on_long_press,
            on_hover,
            ref,
            key,
            width,
            _unwrap_value(height),
            left,
            top, 
            right,
            bottom,
            expand,
            expand_loose,
            col,
            _unwrap_value(opacity),
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            tooltip,
            badge,
            visible,
            _unwrap_value(disabled),
            data,
            rtl,
            adaptive
        )

        if isinstance(bgcolor, State):
            self._new_stateful_prop_binding(bgcolor, self, 'bgcolor')
        if isinstance(border, State):
            self._new_stateful_prop_binding(border, self, 'border')
        if isinstance(height, State):
            self._new_stateful_prop_binding(height, self, 'height')
        if isinstance(opacity, State):
            self._new_stateful_prop_binding(opacity, self, 'opacity')
        if isinstance(disabled, State):
            self._new_stateful_prop_binding(disabled, self, 'disabled')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveStack(ft.Stack, _ReactiveControlWrapper):
    def __init__(self, 
        controls: Sequence[ft.Control] | None = None,
        clip_behavior: ft.ClipBehavior | None = None,
        alignment: ft.Alignment | None = None,
        fit: ft.StackFit | None = None,
        ref: ft.Ref | None = None,
        key: str | None = None,
        width: int | float | None = None,
        height: int | float | None = None,
        left: int | float | None = None,
        top: int | float | None = None,
        right: int | float | None = None,
        bottom: int | float | None = None,
        expand: None | bool | int = None,
        expand_loose: bool | None = None,
        col: Dict[str, int | float] | int | float | None = None,
        opacity: int | float | None = None,
        rotate: int | float | ft.Rotate | None = None,
        scale: int | float | ft.Scale | None = None,
        offset: ft.Offset | None = None,
        aspect_ratio: int | float | None = None,
        animate_opacity: bool | int | ft.Animation | None = None,
        animate_size: bool | int | ft.Animation | None = None,
        animate_position: bool | int | ft.Animation | None = None,
        animate_rotation: bool | int | ft.Animation | None = None,
        animate_scale: bool | int | ft.Animation | None = None,
        animate_offset: bool | int | ft.Animation | None = None,
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None,
        visible: bool | None | State[bool | None] = None,
        disabled: bool | None = None,
        data: Any = None,
        adaptive: bool | None = None
    ):
        super().__init__(
            controls,
            clip_behavior,
            alignment,
            fit,
            ref,
            key,
            width,
            height,
            left,
            top,
            right, 
            bottom,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            _unwrap_value(visible),
            disabled,
            data,
            adaptive
        )

        if isinstance(visible, State):
            self._new_stateful_prop_binding(visible, self, 'visible')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveDropdown(ft.Dropdown, _ReactiveControlWrapper):
    def __init__(self, 
        value: str | None | State[str | None] = None,
        autofocus: bool | None = None,
        text_align: ft.TextAlign | None = None,
        elevation: None | int | float | Dict[ft.ControlState, int | float | None] = None,
        options: List[ft.DropdownOption] | None = None,
        label_content: str | None = None,
        enable_filter: bool | None = None,
        enable_search: bool | None = None,
        editable: bool | None = None,
        max_menu_height: int | float | None = None,
        menu_height: int | float | None = None,
        menu_width: int | float | None = None,
        expanded_insets: int | float | ft.Padding | None = None,
        selected_suffix: ft.Control | None = None,
        input_filter: ft.InputFilter | None = None,
        capitalization: ft.TextCapitalization | None = None,
        options_fill_horizontally: bool | None = None,
        padding: int | float | ft.Padding | None = None,
        trailing_icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None,
        leading_icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None,
        select_icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None,
        selected_trailing_icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None,
        on_change: Callable[[Any], Any] | None = None,
        on_focus: Callable[[Any], Any] | None = None,
        on_blur: Callable[[Any], Any] | None = None,
        enable_feedback: bool | None = None,
        item_height: int | float | None = None,
        alignment: ft.Alignment | None = None,
        hint_content: ft.Control | None = None,
        icon_content: ft.Control | None = None,
        select_icon_size: int | float | None = None,
        icon_size: int | float | None = None,
        select_icon_enabled_color: str | ft.Colors | ft.CupertinoColors | None = None,
        icon_enabled_color: str | ft.Colors | ft.CupertinoColors | None = None,
        select_icon_disabled_color: str | ft.Colors | ft.CupertinoColors | None = None,
        icon_disabled_color: str | ft.Colors | ft.CupertinoColors | None = None,
        bgcolor: str | ft.Colors | ft.CupertinoColors | None = None,
        error_style: ft.TextStyle | None = None,
        error_text: str | None = None,
        text_size: int | float | None = None,
        text_style: ft.TextStyle | None = None,
        label: str | None = None,
        label_style: ft.TextStyle | None = None,
        icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None,
        border: ft.InputBorder | None = None,
        color: str | None = None,
        focused_color: str | None = None,
        focused_bgcolor: str | None = None,
        border_width: int | float | None = None,
        border_color: str | None = None,
        border_radius: int | float | ft.BorderRadius | None = None,
        focused_border_width: int | float | None = None,
        focused_border_color: str | None = None,
        content_padding: int | float | ft.Padding | None = None,
        dense: bool | None = None,
        filled: bool | None = None,
        fill_color: str | None = None,
        hover_color: str | None = None,
        hint_text: str | None = None,
        hint_style: ft.TextStyle | None = None,
        helper_text: str | None = None,
        helper_style: ft.TextStyle | None = None,
        prefix: ft.Control | None = None,
        prefix_text: str | None = None,
        prefix_style: ft.TextStyle | None = None,
        prefix_icon: str | None = None,
        disabled_hint_content: ft.Control | None = None,
        suffix: ft.Control | None = None,
        suffix_icon: str | ft.Icons | ft.CupertinoIcons | Any | None = None,
        suffix_text: str | None = None,
        suffix_style: ft.TextStyle | None = None,
        counter: ft.Control | None = None,
        counter_text: str | None = None,
        counter_style: ft.TextStyle | None = None,
        ref: ft.Ref | None = None,
        key: str | None = None,
        width: int | float | None = None,
        expand: None | bool | int = None,
        expand_loose: bool | None = None,
        col: Dict[str, int | float] | int | float | None = None,
        opacity: int | float | None = None,
        rotate: int | float | ft.RotateValue | None = None,
        scale: int | float | ft.Scale | None = None,
        offset: ft.Offset | None = None,
        aspect_ratio: int | float | None = None,
        animate_opacity: bool | int | ft.Animation | None = None,
        animate_size: bool | int | ft.Animation | None = None,
        animate_position: bool | int | ft.Animation | None = None,
        animate_rotation: bool | int | ft.Animation | None = None,
        animate_scale: bool | int | ft.Animation | None = None,
        animate_offset: bool | int | ft.Animation | None = None,
        on_animation_end: Callable[[Any], Any] | None = None,
        tooltip: str | None = None,
        visible: bool | None = None,
        disabled: bool | None = None,
        data: Any = None
    ):
        super().__init__(
            _unwrap_value(value),
            autofocus,
            text_align,
            elevation,
            options, # type: ignore
            label_content,
            enable_filter,
            enable_search,
            editable,
            max_menu_height,
            menu_height,
            menu_width,
            expanded_insets, # type: ignore
            selected_suffix,
            input_filter,
            capitalization,
            options_fill_horizontally,
            padding,
            trailing_icon,
            leading_icon,
            select_icon,
            selected_trailing_icon,
            on_change,
            on_focus,
            on_blur,
            enable_feedback,
            item_height,
            alignment,
            hint_content,
            icon_content,
            select_icon_size,
            icon_size,
            select_icon_enabled_color,
            icon_enabled_color,
            select_icon_disabled_color,
            icon_disabled_color,
            bgcolor,
            error_style,
            error_text,
            text_size,
            text_style,
            label,
            label_style,
            icon,
            border,
            color,
            focused_color,
            focused_bgcolor,
            border_width,
            border_color,
            border_radius,
            focused_border_width,
            focused_border_color,
            content_padding, # type: ignore
            dense,
            filled,
            fill_color,
            hover_color,
            hint_text,
            hint_style,
            helper_text,
            helper_style,
            prefix,
            prefix_text,
            prefix_style,
            prefix_icon,
            disabled_hint_content,
            suffix,
            suffix_icon,
            suffix_text,
            suffix_style,
            counter,
            counter_text,
            counter_style,
            ref,
            key,
            width,
            expand,
            expand_loose,
            col,
            opacity,
            rotate, # type: ignore
            scale, # type: ignore
            offset, # type: ignore
            aspect_ratio,
            animate_opacity, # type: ignore
            animate_size, # type: ignore
            animate_position, # type: ignore
            animate_rotation, # type: ignore
            animate_scale, # type: ignore
            animate_offset, # type: ignore
            on_animation_end,
            tooltip,
            visible,
            disabled,
            data
        )

        if isinstance(value, State):
            binding = self._new_stateful_prop_binding(value, self, 'value')
            self.on_change = lambda ev: (
                binding.sync_state(),
                on_change(ev) if on_change else None
            )

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveRow(ft.Row, _ReactiveControlWrapper):
    def __init__(self, 
        controls: Sequence[ft.Control] | None = None, 
        alignment: ft.MainAxisAlignment | None = None, 
        vertical_alignment: ft.CrossAxisAlignment | None = None, 
        spacing: int | float | None = None, 
        tight: bool | None = None, 
        wrap: bool | None = None, 
        run_spacing: int | float | None = None, 
        run_alignment: ft.MainAxisAlignment | None = None, 
        scroll: ft.ScrollMode | None = None, 
        auto_scroll: bool | None = None, 
        on_scroll_interval: int | float | None = None, 
        on_scroll: Callable[[ft.OnScrollEvent], Any] | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None | State[int | float | None] = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        visible: bool | None | State[bool | None] = None, 
        disabled: bool | None | State[bool | None] = None, 
        data: Any = None, 
        rtl: bool | None = None, 
        adaptive: bool | None = None
    ):
        super().__init__(
            controls, 
            alignment, 
            vertical_alignment, 
            spacing, 
            tight, 
            wrap, 
            run_spacing, 
            run_alignment, 
            scroll, 
            auto_scroll, 
            on_scroll_interval, 
            on_scroll, 
            ref, 
            key, 
            width, 
            height, 
            left, 
            top, 
            right, 
            bottom, 
            expand, 
            expand_loose, 
            col, 
            _unwrap_value(opacity), 
            rotate, 
            scale, 
            offset, 
            aspect_ratio, 
            animate_opacity, 
            animate_size, 
            animate_position, 
            animate_rotation, 
            animate_scale, 
            animate_offset, 
            on_animation_end, 
            _unwrap_value(visible), 
            _unwrap_value(disabled), 
            data, 
            rtl, 
            adaptive
        )

        if isinstance(opacity, State):
            self._new_stateful_prop_binding(opacity, self, 'opacity')
        if isinstance(visible, State):
            self._new_stateful_prop_binding(visible, self, 'visible')
        if isinstance(disabled, State):
            self._new_stateful_prop_binding(disabled, self, 'disabled')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()

class ReactiveText(ft.Text, _ReactiveControlWrapper):
    def __init__(self, 
        value: str | None | State[str | None] = None, 
        spans: List[ft.TextSpan] | None = None, 
        text_align: ft.TextAlign | None = None, 
        font_family: str | None = None, 
        size: int | float | None = None, 
        weight: ft.FontWeight | None = None, 
        italic: bool | None = None, 
        style: ft.TextThemeStyle | ft.TextStyle | None = None, 
        theme_style: ft.TextThemeStyle | None = None, 
        max_lines: int | None = None, 
        overflow: ft.TextOverflow | None = None, 
        selectable: bool | None = None, 
        no_wrap: bool | None = None, 
        color: ft.ColorValue | None | State[ft.ColorValue | None] = None, 
        bgcolor: ft.ColorValue | None = None, 
        semantics_label: str | None = None, 
        show_selection_cursor: bool | None = None, 
        enable_interactive_selection: bool | None = None, 
        selection_cursor_width: int | float | None = None, 
        selection_cursor_height: int | float | None = None, 
        selection_cursor_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        on_tap: Callable[[ft.ControlEvent], Any] | None = None, 
        on_selection_change: Callable[[TextSelectionChangeEvent], Any] | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None = None, 
        data: Any = None, 
        rtl: bool | None = None
    ):
        super().__init__(
            _unwrap_value(value), 
            spans, 
            text_align, 
            font_family, 
            size, 
            weight, 
            italic, 
            style, 
            theme_style, 
            max_lines, 
            overflow, 
            selectable, 
            no_wrap, 
            _unwrap_value(color), 
            bgcolor, 
            semantics_label, 
            show_selection_cursor, 
            enable_interactive_selection, 
            selection_cursor_width, 
            selection_cursor_height, 
            selection_cursor_color, 
            on_tap, 
            on_selection_change, 
            ref, 
            key, 
            width, 
            height, 
            left, 
            top, 
            right, 
            bottom, 
            expand, 
            expand_loose, 
            col, 
            opacity, 
            rotate, 
            scale, 
            offset, 
            aspect_ratio, 
            animate_opacity, 
            animate_size, 
            animate_position, 
            animate_rotation, 
            animate_scale, 
            animate_offset, 
            on_animation_end, 
            tooltip, 
            badge, 
            visible, 
            disabled, 
            data, 
            rtl
        )

        if isinstance(value, State):
            self._new_stateful_prop_binding(value, self, 'value')
        if isinstance(color, State):
            self._new_stateful_prop_binding(color, self, 'color')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveIcon(ft.Icon, _ReactiveControlWrapper):
    def __init__(self,
        name: ft.IconValue | None | State[ft.IconValue | None] = None,
        color: ft.ColorValue | None | State[ft.ColorValue | None] = None,
        size: int | float | None = None,
        semantics_label: str | None = None,
        shadows: ft.BoxShadow | List[ft.BoxShadow] | None = None,
        fill: int | float | None = None,
        apply_text_scaling: bool | None = None,
        grade: int | float | None = None,
        weight: int | float | None = None,
        optical_size: int | float | None = None,
        blend_mode: ft.BlendMode | None = None,
        ref: ft.Ref | None = None,
        key: str | None = None,
        expand: None | bool | int = None,
        expand_loose: bool | None = None,
        col: Dict[str, int | float] | int | float | None = None,
        opacity: int | float | None = None,
        rotate: int | float | ft.Rotate | None = None,
        scale: int | float | ft.Scale | None = None,
        offset: ft.Offset | None = None,
        aspect_ratio: int | float | None = None,
        animate_opacity: bool | int | ft.Animation | None = None,
        animate_size: bool | int | ft.Animation | None = None,
        animate_position: bool | int | ft.Animation | None = None,
        animate_rotation: bool | int | ft.Animation | None = None,
        animate_scale: bool | int | ft.Animation | None = None,
        animate_offset: bool | int | ft.Animation | None = None,
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None,
        tooltip: str | ft.Tooltip | None = None,
        badge: str | ft.Badge | None = None,
        visible: bool | None = None,
        disabled: bool | None = None,
        data: Any = None
    ):
        super().__init__(
            _unwrap_value(name),
            _unwrap_value(color),
            size,
            semantics_label,
            shadows,
            fill,
            apply_text_scaling,
            grade,
            weight,
            optical_size,
            blend_mode,
            ref,
            key,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            tooltip,
            badge,
            visible,
            disabled,
            data
        )

        if isinstance(name, State):
            self._new_stateful_prop_binding(name, self, 'name')
        if isinstance(color, State):
            self._new_stateful_prop_binding(color, self, 'color')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveImage(ft.Image, _ReactiveControlWrapper):
    def __init__(self, 
        src: str | None = None, 
        src_base64: str | None = None, 
        error_content: ft.Control | None = None, 
        repeat: ft.ImageRepeat | None = None, 
        fit: ft.ImageFit | None = None, 
        border_radius: int | float | ft.BorderRadius | None = None, 
        color: str | ft.Colors | ft.CupertinoColors | None | State[str | ft.Colors | ft.CupertinoColors | None] = None, 
        color_blend_mode: ft.BlendMode | None = None, 
        gapless_playback: bool | None = None, 
        semantics_label: str | None = None, 
        exclude_from_semantics: bool | None = None, 
        filter_quality: ft.FilterQuality | None = None, 
        cache_width: int | None = None, 
        cache_height: int | None = None, 
        anti_alias: bool | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None = None, 
        data: Any = None
    ):
        super().__init__(
            src,
            src_base64,
            error_content,
            repeat,
            fit,
            border_radius,
            _unwrap_value(color),
            color_blend_mode,
            gapless_playback,
            semantics_label,
            exclude_from_semantics,
            filter_quality,
            cache_width,
            cache_height,
            anti_alias,
            ref,
            key,
            width,
            height,
            left,
            top,
            right,
            bottom,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            tooltip,
            badge,
            visible,
            disabled,
            data
        )

        if isinstance(color, State):
            self._new_stateful_prop_binding(color, self, 'color')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveSwitch(ft.Switch, _ReactiveControlWrapper):
    def __init__(self, 
        label: str | ft.Control | None = None, 
        label_position: ft.LabelPosition | None = None, 
        label_style: ft.TextStyle | None = None, 
        value: bool | None | State[bool | None] = None, 
        autofocus: bool | None = None, 
        active_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        active_track_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        focus_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        inactive_thumb_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        inactive_track_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        thumb_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        thumb_icon: None | str | ft.Icons | ft.CupertinoIcons | Dict[ft.ControlState, str | ft.Icons | ft.CupertinoIcons] = None, 
        track_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        adaptive: bool | None = None, 
        hover_color: str | ft.Colors | ft.CupertinoColors | None = None, 
        splash_radius: int | float | None = None, 
        overlay_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        track_outline_color: None | str | ft.Colors | ft.CupertinoColors | Dict[ft.ControlState, str | ft.Colors | ft.CupertinoColors] = None, 
        track_outline_width: None | int | float | Dict[ft.ControlState, int | float | None] = None, 
        mouse_cursor: ft.MouseCursor | None = None, 
        on_change: Callable[[ft.ControlEvent], Any] | None = None, 
        on_focus: Callable[[ft.ControlEvent], Any] | None = None, 
        on_blur: Callable[[ft.ControlEvent], Any] | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None = None, 
        data: Any = None
    ):
        super().__init__(
            label,
            label_position,
            label_style,
            _unwrap_value(value),
            autofocus,
            active_color,
            active_track_color,
            focus_color,
            inactive_thumb_color,
            inactive_track_color,
            thumb_color,
            thumb_icon,
            track_color,
            adaptive,
            hover_color,
            splash_radius,
            overlay_color,
            track_outline_color,
            track_outline_width,
            mouse_cursor,
            on_change,
            on_focus,
            on_blur,
            ref,
            key,
            width,
            height,
            left,
            top,
            right,
            bottom,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            tooltip,
            badge,
            visible,
            disabled,
            data
        )

        if isinstance(value, State):
            binding = self._new_stateful_prop_binding(value, self, 'value')
            self.on_change = lambda ev: (
                binding.sync_state(),
                on_change(ev) if on_change else None
            )

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()



class ReactiveProgressRing(ft.ProgressRing, _ReactiveControlWrapper):
    def __init__(self, 
        value: int | float | None | State[int | float | None] = None, 
        stroke_width: int | float | None = None, 
        color: str | ft.Colors | ft.CupertinoColors | None = None, 
        bgcolor: str | ft.Colors | ft.CupertinoColors | None = None, 
        stroke_align: int | float | None = None, 
        stroke_cap: ft.StrokeCap | None = None, 
        semantics_label: str | None = None, 
        semantics_value: int | float | None = None, 
        track_gap: int | float | None = None, 
        size_constraints: ft.BoxConstraints | None = None, 
        padding: int | float | ft.Padding | None = None, 
        year_2023: bool | None = None, 
        ref: ft.Ref | None = None, 
        key: str | None = None, 
        width: int | float | None = None, 
        height: int | float | None = None, 
        left: int | float | None = None, 
        top: int | float | None = None, 
        right: int | float | None = None, 
        bottom: int | float | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: Dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        rotate: int | float | ft.Rotate | None = None, 
        scale: int | float | ft.Scale | None = None, 
        offset: ft.Offset | None = None, 
        aspect_ratio: int | float | None = None, 
        animate_opacity: bool | int | ft.Animation | None = None, 
        animate_size: bool | int | ft.Animation | None = None, 
        animate_position: bool | int | ft.Animation | None = None, 
        animate_rotation: bool | int | ft.Animation | None = None, 
        animate_scale: bool | int | ft.Animation | None = None, 
        animate_offset: bool | int | ft.Animation | None = None, 
        on_animation_end: Callable[[ft.ControlEvent], Any] | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None | State[bool | None] = None, 
        disabled: bool | None = None, 
        data: Any = None
    ):
        super().__init__(
            _unwrap_value(value),
            stroke_width,
            color,
            bgcolor,
            stroke_align,
            stroke_cap,
            semantics_label,
            semantics_value,
            track_gap,
            size_constraints,
            padding,
            year_2023,
            ref,
            key,
            width,
            height,
            left,
            top,
            right,
            bottom,
            expand,
            expand_loose,
            col,
            opacity,
            rotate,
            scale,
            offset,
            aspect_ratio,
            animate_opacity,
            animate_size,
            animate_position,
            animate_rotation,
            animate_scale,
            animate_offset,
            on_animation_end,
            tooltip,
            badge,
            _unwrap_value(visible),
            disabled,
            data
        )

        if isinstance(value, State):
            self._new_stateful_prop_binding(value, self, 'value')
        if isinstance(visible, State):
            self._new_stateful_prop_binding(visible, self, 'visible')

    def build(self):
        super().build()
        self._init_prop_bindings()

    def will_unmount(self):
        super().will_unmount()
        self._drop_prop_bindings()