export interface Choice {
  id: string;
  label: string;
}

export interface Message {
  id: string;
  role: "bot" | "user";
  text: string;
  quickReplies?: string[];
  type?: "text" | "multipleChoice";
  choices?: Choice[];
}
