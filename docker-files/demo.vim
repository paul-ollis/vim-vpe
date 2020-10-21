py3 <<EOF
text = r'''
 #####                                            
#     # #    #  ####   ####  ######  ####   ####  
#       #    # #    # #    # #      #      #      
 #####  #    # #      #      #####   ####   ####  
      # #    # #      #      #           #      # 
#     # #    # #    # #    # #      #    # #    # 
 #####   ####   ####   ####  ######  ####   ####  
'''
                               
from vpe import vim
with vim.current.buffer.list() as lines:
    lines[:] = text.splitlines()
EOF
