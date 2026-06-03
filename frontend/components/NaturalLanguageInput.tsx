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
      <span className="mb-1.5 block">Trip Request</span>
      <textarea
        className="min-h-40 w-full resize-y rounded-md border border-slate-300 px-3 py-2.5 text-slate-950 outline-none ring-teal-600 focus:ring-2"
        placeholder={DEFAULT_NATURAL_LANGUAGE_MESSAGE}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
      />
    </label>
  );
}
