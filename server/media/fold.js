
function foldunfold(folded, unfolded)
{
  ff = document.getElementById(folded);
  uf = document.getElementById(unfolded);
  i_ff = document.getElementById('img_' + folded);
  i_uf = document.getElementById('img_' + unfolded);
  
  if (!ff)
  {
    alert("Cannot find " + folded);
    return;
  }
  
  if (!uf)
  {
    alert("Cannot find " + unfolded);
    return;
  }
  
  if (ff.style.display == 'none')
  {
    ff.style.display = '';
    uf.style.display = 'none';
  } else {
    ff.style.display = 'none';
    uf.style.display = '';
  }
  
  if (i_ff && i_uf)
  {
    if (i_ff.style.display == 'none')
    {
      i_ff.style.display = 'inline';
      i_uf.style.display = 'none';
    } else {
      i_ff.style.display = 'none';
      i_uf.style.display = 'inline';
    }
  }
}
