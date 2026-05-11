export interface Choice {
  id: string;
  label: string;
}

export interface Product {
  name: string;
  sku: string;
  description: string;
}

export interface Message {
  id: string;
  role: "bot" | "user";
  text: string;
  quickReplies?: string[];
  type?: "text" | "multipleChoice";
  choices?: Choice[];
  answered?: boolean;
  selectedChoice?: string;
  product?: Product;
  collectedInfo?: Record<string, unknown>;
  nextState?: string;
}
