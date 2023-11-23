import Link from "next/link";

function NavListItem({ title, link, state, makeActive }) {
	return (
		<button
			className={`rounded-2xl border-l-[5px] bg-[var(--color-secondary)] ${
				state == link ? "border-[var(--color-tertiary)]" : "border-[var(--color-secondary)]"
			}`}
			onClick={() => makeActive(link)}
		>
			<Link
				href={link}
				className={`block bg-[var(--color-secondary)] bg-opacity-20 px-10 py-3 rounded-2xl font-bold text-[var(--color-text)] cursor-pointer`}
			>
				{title}
			</Link>
		</button>
	);
}

export default NavListItem;
