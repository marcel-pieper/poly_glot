import ExpoModulesCore

public class SelectionActionsModule: Module {
  public func definition() -> ModuleDefinition {
    Name("SelectionActions")

    View(SelectableTranslateTextView.self) {
      Events("onTranslate")

      Prop("text") { (view: SelectableTranslateTextView, value: String) in
        view.setText(value)
      }

      Prop("fontSize") { (view: SelectableTranslateTextView, value: Double?) in
        view.setFontSize(value ?? 15)
      }

      Prop("color") { (view: SelectableTranslateTextView, value: String?) in
        view.setTextColorHex(value)
      }

      Prop("translateLabel") { (view: SelectableTranslateTextView, value: String?) in
        view.setTranslateLabel(value ?? "Translate")
      }
    }
  }
}
