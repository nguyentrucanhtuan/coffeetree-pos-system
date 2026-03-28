"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { FieldBaseProps } from ".";
import { useEffect } from "react";
import { cn } from "@/lib/utils";
import { 
  Bold, 
  Italic, 
  List, 
  ListOrdered, 
  Heading1, 
  Heading2, 
  Quote 
} from "lucide-react";

export function RichTextField({ value, onChange, disabled, error }: FieldBaseProps) {
  const editor = useEditor({
    extensions: [StarterKit],
    content: value || "",
    editable: !disabled,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value || "");
    }
  }, [value, editor]);

  if (!editor) return null;

  const Toolbar = () => (
    <div className="flex flex-wrap gap-1 p-1 bg-muted/50 rounded-t-md border-b border-border/10">
      <ToolbarButton 
        onClick={() => editor.chain().focus().toggleBold().run()} 
        active={editor.isActive("bold")}
        icon={<Bold className="size-3" />}
      />
      <ToolbarButton 
        onClick={() => editor.chain().focus().toggleItalic().run()} 
        active={editor.isActive("italic")}
        icon={<Italic className="size-3" />}
      />
      <div className="w-px h-4 bg-border/20 mx-1 self-center" />
      <ToolbarButton 
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} 
        active={editor.isActive("heading", { level: 1 })}
        icon={<Heading1 className="size-3" />}
      />
      <ToolbarButton 
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} 
        active={editor.isActive("heading", { level: 2 })}
        icon={<Heading2 className="size-3" />}
      />
      <div className="w-px h-4 bg-border/20 mx-1 self-center" />
      <ToolbarButton 
        onClick={() => editor.chain().focus().toggleBulletList().run()} 
        active={editor.isActive("bulletList")}
        icon={<List className="size-3" />}
      />
      <ToolbarButton 
        onClick={() => editor.chain().focus().toggleOrderedList().run()} 
        active={editor.isActive("orderedList")}
        icon={<ListOrdered className="size-3" />}
      />
      <ToolbarButton 
        onClick={() => editor.chain().focus().toggleBlockquote().run()} 
        active={editor.isActive("blockquote")}
        icon={<Quote className="size-3" />}
      />
    </div>
  );

  return (
    <div className={cn(
      "flex flex-col rounded-md border bg-background transition-all",
      editor.isFocused && "ring-1 ring-ring border-ring",
      error && "border-destructive ring-destructive"
    )}>
      <Toolbar />
      <EditorContent 
        editor={editor} 
        className="prose prose-sm max-w-none p-3 min-h-[120px] focus:outline-none overflow-y-auto"
      />
      {error && <p className="text-[10px] font-medium text-destructive px-3 pb-1.5">{error}</p>}
    </div>
  );
}

function ToolbarButton({ onClick, active, icon }: { onClick: () => void, active: boolean, icon: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "p-1.5 rounded-sm hover:bg-muted transition-colors flex items-center justify-center",
        active ? "bg-muted text-primary font-bold shadow-sm" : "text-muted-foreground/60"
      )}
    >
      {icon}
    </button>
  );
}
