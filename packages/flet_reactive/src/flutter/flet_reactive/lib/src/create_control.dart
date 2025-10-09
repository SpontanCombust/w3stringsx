import 'package:flet/flet.dart';

import 'flet_reactive.dart';

CreateControlFactory createControl = (CreateControlArgs args) {
  switch (args.control.type) {
    case "flet_reactive":
      return FletReactiveControl(
        parent: args.parent,
        control: args.control,
        children: args.children,
        parentDisabled: args.parentDisabled
      );
    default:
      return null;
  }
};

void ensureInitialized() {
  // nothing to initialize
}
