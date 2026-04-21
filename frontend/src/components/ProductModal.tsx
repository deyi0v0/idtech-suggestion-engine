import { useEffect } from "react";
import type { Product } from "../types/messages";

interface ProductModalProps {
  product: Product;
  onClose: () => void;
}

export default function ProductModal({ product, onClose }: ProductModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-1/2 max-h-[80vh] overflow-y-auto p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-2xl font-bold mb-2">Recommended Products</h2>
        <p className="text-gray-500 mb-6">Based on your responses, here are our top picks.</p>

        <div className="border border-gray-200 rounded-xl p-4 mb-4">
          <h3 className="text-lg font-semibold">{product.name} — SKU: {product.sku}</h3>
          <p className="text-gray-600 mt-1 text-sm">{product.description}</p>
        </div>

        <button
          onClick={onClose}
          className="mt-2 text-sm text-gray-400 hover:text-gray-600 underline cursor-pointer"
        >
          Close
        </button>
      </div>
    </div>
  );
}
