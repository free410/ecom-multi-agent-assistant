interface ExamplePromptsProps {
  prompts: string[];
  onSelect: (prompt: string) => void;
}

export function ExamplePrompts({ prompts, onSelect }: ExamplePromptsProps) {
  return (
    <section className="panel examples-panel">
      <div className="panel-header">
        <h2>商品示例区</h2>
      </div>
      <div className="example-list">
        {prompts.map((item) => (
          <button key={item} className="example-item" onClick={() => onSelect(item)}>
            {item}
          </button>
        ))}
      </div>
    </section>
  );
}

