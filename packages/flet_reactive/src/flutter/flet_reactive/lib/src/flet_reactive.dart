import 'package:flet/flet.dart';
import 'package:flutter/material.dart';

class FletReactiveControl extends StatelessWidget {
  final Control? parent;
  final Control control;
  final List<Control> children;
  final bool parentDisabled;

  const FletReactiveControl({
    super.key,
    required this.parent,
    required this.control,
    required this.children,
    required this.parentDisabled,
  });

  @override
  Widget build(BuildContext context) {
    bool disabled = control.isDisabled || parentDisabled;
    var contentCtrls = 
      children.where((c) => c.name == "content" && c.isVisible);
    Widget child = createControl(control, contentCtrls.first.id, disabled);

    return baseControl(context, child, parent, control);
  }
}
