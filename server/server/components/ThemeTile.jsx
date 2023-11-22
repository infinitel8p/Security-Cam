import { useTitleCase } from "@/hooks/useTitleCase";

function ThemeTile({ name, handleClick }) {
	return (
		<div
			data-theme={name}
			className="bg-[var(--color-primary)] text-[var(--color-text)] flex border border-[var(--color-tertiary)] rounded-xl p-5 justify-between items-center"
		>
			<input type="radio" id={name} name="colortheme" className={`hidden peer/${name}`} />
			<label className={`font-semibold`} htmlFor={name}>
				{useTitleCase(name)}
			</label>
			<div
				onClick={() => {
					handleClick(name);
				}}
				className={`bg-[var(--color-tertiary)] rounded-full flex items-center justify-center px-5 py-2 font-bold peer-checked/${name}:hidden cursor-pointer`}
			>
				Select Theme
			</div>
		</div>
	);
}

export default ThemeTile;
