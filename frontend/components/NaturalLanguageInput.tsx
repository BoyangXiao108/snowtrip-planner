import { DEFAULT_NATURAL_LANGUAGE_MESSAGE } from "../constants";

export function NaturalLanguageInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-sm font-medium text-slate-800">
      <span className="mb-2 block">Trip Request</span>
      <textarea
        className="min-h-56 w-full resize-y rounded-xl border border-slate-200 bg-white px-4 py-3 text-base leading-7 text-slate-950 shadow-sm outline-none ring-teal-600 placeholder:text-slate-400 focus:ring-2"
        placeholder={DEFAULT_NATURAL_LANGUAGE_MESSAGE}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
      />
    </label>
  );
}
