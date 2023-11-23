"use client";
import NavListItem from "./NavListItem";

function NavList({ state, makeActive }) {
	return (
		<nav className="flex flex-col gap-12 list-none">
			<NavListItem title="Home" link="/" makeActive={makeActive} state={state} />
			<NavListItem title="Info" link="/info" makeActive={makeActive} state={state} />
			<NavListItem title="Archive" link="/archive" makeActive={makeActive} state={state} />
			<NavListItem title="Settings" link="/settings" makeActive={makeActive} state={state} />
		</nav>
	);
}

export default NavList;
