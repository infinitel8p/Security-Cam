"use client";
import { useState } from 'react';
import NavListItem from './NavListItem'

function NavList() {

  const [active, setActive] = useState('Home');

  const makeActive = (title) => {
    setActive(title);
  }

  return (
    <nav className='flex flex-col gap-12 list-none'>
        <NavListItem title="Home" link="/" makeActive={makeActive} state={active} />
        <NavListItem title="Info" link="/info" makeActive={makeActive} state={active} />
        <NavListItem title="Archive" link="/archive" makeActive={makeActive} state={active} />
        <NavListItem title="Settings" link="/settings" makeActive={makeActive} state={active} />
    </nav>
  )
}

export default NavList